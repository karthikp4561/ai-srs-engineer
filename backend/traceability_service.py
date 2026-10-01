import json
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from models import Project, GitHubConnection
from ai_service import generate_traceability_matrix_ai


STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "of", "at", "by", "for",
    "with", "about", "against", "between", "into", "through", "during", "before",
    "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off",
    "over", "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "any", "both", "each", "few", "more", "most",
    "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "can", "will", "just", "should", "now", "must", "be",
    "able", "system", "shall", "allow", "provide", "support", "using", "user", "users"
}

AMBIGUITY_PATTERNS = [
    (r"\buser[- ]friendly\b", "Subjective usability metric ('user-friendly')"),
    (r"\bseamless(?:ly)?\b", "Unquantified performance descriptor ('seamless')"),
    (r"\befficient(?:ly)?\b", "Unquantified performance claim ('efficient')"),
    (r"\bfast(?:er)?\b", "Unspecified latency target ('fast')"),
    (r"\bquick(?:ly)?\b", "Unspecified latency target ('quickly')"),
    (r"\brobust(?:ly)?\b", "Vague reliability claim ('robust')"),
    (r"\bflexib(?:le|ility)\b", "Subjective architectural goal ('flexible')"),
    (r"\bappropriate(?:ly)?\b", "Subjective standard ('appropriate')"),
    (r"\betc\.?\b", "Incomplete requirement enumeration ('etc.')"),
    (r"\band so forth\b", "Incomplete requirement enumeration ('and so forth')"),
    (r"\boptimal(?:ly)?\b", "Unquantified optimization metric ('optimal')"),
    (r"\bas soon as possible\b", "Indefinite timing constraint ('ASAP')"),
    (r"\breal[- ]time\b", "Unspecified latency constraint ('real-time' without SLA)"),
]


def _detect_ambiguity(text: str) -> List[str]:
    flags = []
    for pattern, note in AMBIGUITY_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            flags.append(note)
    return flags


def _normalize_text(text: str) -> str:
    t = text.lower()
    t = re.sub(r"\blog\s+in\b", "login", t)
    t = re.sub(r"\bsign\s+in\b", "signin login", t)
    t = re.sub(r"\bsign\s+up\b", "signup register", t)
    t = re.sub(r"\bauth(?:enticat\w*)?\b", "auth authentication authenticate login", t)
    return t


def _extract_keywords(text: str) -> set:
    norm = _normalize_text(text)
    words = re.findall(r"\b[A-Za-z]{3,}\b", norm)
    keywords = set()
    for w in words:
        if w not in STOP_WORDS:
            keywords.add(w)
            if len(w) > 4:
                stem = re.sub(r"(?:ing|tion|ed|es|s)$", "", w)
                if len(stem) >= 3 and stem not in STOP_WORDS:
                    keywords.add(stem)
    return keywords


def _has_keyword_overlap(set1: set, set2: set) -> bool:
    if set1 & set2:
        return True
    for w1 in set1:
        for w2 in set2:
            if len(w1) >= 4 and len(w2) >= 4:
                if w1.startswith(w2) or w2.startswith(w1):
                    return True
    return False


def _extract_diagram_components(diagrams: Optional[dict]) -> List[str]:
    """Extract named nodes, classes, and tables from Mermaid diagrams."""
    if not diagrams:
        return []
    components = []
    
    # 1. Use case diagram elements
    use_case = diagrams.get("use_case_diagram", "")
    if use_case:
        # Match nodes like id(Label) or id([Label])
        uc_matches = re.findall(r"\((?:\[)?([^\]\(\)\n]+?)(?:\])?\)", use_case)
        for m in uc_matches:
            clean = m.strip().strip('"').strip("'")
            if clean and len(clean) > 2 and not clean.startswith("graph ") and not clean.startswith("subgraph"):
                components.append(f"Use Case: {clean}")

    # 2. Class diagram elements
    class_diag = diagrams.get("class_diagram", "")
    if class_diag:
        class_matches = re.findall(r"\bclass\s+([A-Za-z0-9_]+)", class_diag)
        for c in class_matches:
            components.append(f"Class: {c}")

    # 3. ER diagram elements
    er_diag = diagrams.get("er_diagram", "")
    if er_diag:
        er_matches = re.findall(r"\b([A-Za-z0-9_]+)\s*\{", er_diag)
        for t in er_matches:
            if t.upper() not in ("ERDIAGRAM", "GRAPH"):
                components.append(f"ERD: {t}")

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for c in components:
        if c not in seen:
            seen.add(c)
            deduped.append(c)
    return deduped


def _heuristic_match_requirement(
    req: str,
    diagram_components: List[str],
    endpoints: List[dict]
) -> tuple:
    """Fallback heuristic matcher when AI is offline or returns incomplete mappings."""
    req_keywords = _extract_keywords(req)
    
    # Match diagram elements
    matched_diagrams = []
    for comp in diagram_components:
        comp_keywords = _extract_keywords(comp)
        if _has_keyword_overlap(req_keywords, comp_keywords):
            matched_diagrams.append(comp)

    # Match API endpoints
    matched_endpoints = []
    for ep in endpoints:
        path = ep.get("path", "")
        desc = ep.get("description", "")
        method = ep.get("method", "GET").upper()
        ep_keywords = _extract_keywords(f"{path} {desc}")
        if _has_keyword_overlap(req_keywords, ep_keywords):
            matched_endpoints.append(f"{method} {path}")

    # Fallback to general if nothing matched but broad entity exists
    return matched_diagrams[:4], matched_endpoints[:4]


def build_traceability_matrix(project: Project, db: Session) -> dict:
    if not project.analysis_json:
        raise ValueError("Project must be analyzed before generating a traceability matrix.")

    try:
        analysis = json.loads(project.analysis_json)
    except Exception:
        raise ValueError("Invalid project analysis data.")

    requirements = analysis.get("functional_requirements", [])
    if not requirements:
        raise ValueError("No functional requirements found in project analysis.")

    # Load diagrams
    try:
        diagrams = json.loads(project.diagrams_json) if project.diagrams_json else None
    except Exception:
        diagrams = None
    diagram_components = _extract_diagram_components(diagrams)
    diagrams_summary = ""
    if diagrams:
        parts = []
        if diagrams.get("use_case_diagram"):
            parts.append(f"### Use Case Diagram:\n{diagrams['use_case_diagram']}")
        if diagrams.get("class_diagram"):
            parts.append(f"### Class Diagram:\n{diagrams['class_diagram']}")
        if diagrams.get("er_diagram"):
            parts.append(f"### ER Diagram:\n{diagrams['er_diagram']}")
        diagrams_summary = "\n\n".join(parts)

    # Load API spec
    try:
        api_spec = json.loads(project.api_spec_json) if project.api_spec_json else None
    except Exception:
        api_spec = None
    endpoints = api_spec.get("endpoints", []) if api_spec else []
    api_endpoints_summary = ""
    if endpoints:
        api_endpoints_summary = "\n".join(
            f"- {ep.get('method', 'GET').upper()} {ep.get('path', '/')}: {ep.get('description', '')}"
            for ep in endpoints
        )

    # Load GitHub connection
    conn = db.query(GitHubConnection).filter(GitHubConnection.project_id == project.id).first()
    synced_issues = {}
    has_github = False
    if conn and conn.synced_issues_json:
        has_github = True
        try:
            synced_issues = json.loads(conn.synced_issues_json)
        except Exception:
            synced_issues = {}
    elif conn:
        has_github = True

    # Try AI generation first
    ai_mappings_by_index: Dict[int, dict] = {}
    ai_summary = ""
    try:
        ai_result = generate_traceability_matrix_ai(
            requirements=requirements,
            diagrams_summary=diagrams_summary,
            api_endpoints_summary=api_endpoints_summary
        )
        if isinstance(ai_result, dict):
            ai_summary = ai_result.get("validation_summary", "")
            for m in ai_result.get("mappings", []):
                idx = m.get("requirement_index")
                if idx is not None and isinstance(idx, int):
                    ai_mappings_by_index[idx] = m
    except Exception:
        # Fall back to heuristic
        pass

    # Build matrix items
    items = []
    for i, req in enumerate(requirements):
        req_id = f"REQ-{i+1:03d}"
        
        # Diagram elements and API endpoints (from AI or heuristic fallback)
        ai_entry = ai_mappings_by_index.get(i)
        if ai_entry and (ai_entry.get("diagram_elements") or ai_entry.get("api_endpoints")):
            diag_elems = [str(d) for d in ai_entry.get("diagram_elements", [])]
            api_elems = [str(a) for a in ai_entry.get("api_endpoints", [])]
            val_notes = ai_entry.get("validation_notes")
        else:
            h_diag, h_api = _heuristic_match_requirement(req, diagram_components, endpoints)
            diag_elems = h_diag
            api_elems = h_api
            val_notes = None

        # GitHub issue lookup
        issue_url = synced_issues.get(req)
        issue_number = None
        if issue_url:
            m = re.search(r"/issues/(\d+)", issue_url)
            issue_number = f"#{m.group(1)}" if m else "Issue"

        # Check missing artifacts
        missing_artifacts = []
        if not diag_elems:
            missing_artifacts.append("UML Diagram")
        if not api_elems:
            missing_artifacts.append("API Endpoint")
        if has_github and not issue_url:
            missing_artifacts.append("GitHub Issue")

        # Determine status
        has_diag = len(diag_elems) > 0
        has_api = len(api_elems) > 0
        has_issue = bool(issue_url)

        if has_github:
            if has_diag and has_api and has_issue:
                status = "fully_traced"
            elif has_diag or has_api or has_issue:
                status = "partially_traced"
            else:
                status = "untraced"
        else:
            if has_diag and has_api:
                status = "fully_traced"
            elif has_diag or has_api:
                status = "partially_traced"
            else:
                status = "untraced"

        # Calculate coverage score (0.0 to 1.0)
        total_targets = 3 if has_github else 2
        achieved_targets = (1 if has_diag else 0) + (1 if has_api else 0) + (1 if (has_github and has_issue) else 0)
        coverage_score = round(achieved_targets / total_targets, 2)

        # Ambiguity detection on requirement text
        ambiguity_flags = _detect_ambiguity(req)
        is_ambiguous = len(ambiguity_flags) > 0

        if not val_notes:
            if status == "fully_traced":
                val_notes = "Complete downstream traceability established across diagrams, API, and issue tracking."
            elif status == "partially_traced":
                missing_str = ", ".join(missing_artifacts)
                val_notes = f"Partially covered. Missing downstream implementation: {missing_str}."
            else:
                val_notes = "Orphan requirement: no downstream diagram element or API endpoint models this requirement."

        if is_ambiguous:
            warning_tag = f"Quality Alert: Vague term{'s' if len(ambiguity_flags) > 1 else ''} detected ({'; '.join(ambiguity_flags)})."
            val_notes = f"{val_notes} [{warning_tag}]"

        items.append({
            "requirement_id": req_id,
            "requirement_text": req,
            "diagram_elements": diag_elems,
            "api_endpoints": api_elems,
            "github_issue_url": issue_url,
            "github_issue_number": issue_number,
            "status": status,
            "missing_artifacts": missing_artifacts,
            "coverage_score": coverage_score,
            "validation_notes": val_notes,
            "ambiguity_flags": ambiguity_flags,
            "is_ambiguous": is_ambiguous,
        })

    # Summary metrics
    total_reqs = len(items)
    fully_traced = sum(1 for it in items if it["status"] == "fully_traced")
    partially_traced = sum(1 for it in items if it["status"] == "partially_traced")
    untraced = sum(1 for it in items if it["status"] == "untraced")
    diag_cov = sum(1 for it in items if it["diagram_elements"])
    api_cov = sum(1 for it in items if it["api_endpoints"])
    gh_cov = sum(1 for it in items if it["github_issue_url"])
    ambiguous_count = sum(1 for it in items if it["is_ambiguous"])
    
    pct = int((fully_traced / total_reqs) * 100) if total_reqs > 0 else 0
    comp_score = f"{fully_traced} of {total_reqs} requirements fully traced"
    orphaned = [it["requirement_text"] for it in items if it["status"] == "untraced"]

    # Quality score out of 100 based on coverage and ambiguity
    quality_score = 100
    if total_reqs > 0:
        penalty = int((ambiguous_count / total_reqs * 35) + (untraced / total_reqs * 65))
        quality_score = max(0, 100 - penalty)

    if not ai_summary:
        if untraced == 0 and fully_traced == total_reqs:
            ai_summary = f"All {total_reqs} functional requirements have complete forward traceability to diagrams and implementation artifacts."
        elif untraced > 0:
            ai_summary = f"{untraced} requirement{'s' if untraced != 1 else ''} flagged as orphaned without downstream implementation. {fully_traced} of {total_reqs} requirements are fully traced."
        else:
            ai_summary = f"{fully_traced} of {total_reqs} requirements fully verified. {partially_traced} requirement{'s' if partially_traced != 1 else ''} have partial architectural coverage."

    return {
        "items": items,
        "total_requirements": total_reqs,
        "fully_traced_count": fully_traced,
        "partially_traced_count": partially_traced,
        "untraced_count": untraced,
        "diagram_coverage_count": diag_cov,
        "api_coverage_count": api_cov,
        "github_coverage_count": gh_cov,
        "completeness_score": comp_score,
        "completeness_percentage": pct,
        "validation_summary": ai_summary,
        "orphaned_requirements": orphaned,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "requirements_quality_score": quality_score,
        "ambiguous_requirements_count": ambiguous_count,
    }
