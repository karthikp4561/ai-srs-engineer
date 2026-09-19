import json
from sqlalchemy.orm import Session
from models import Project, ProjectVersion


def snapshot_fields(project: Project) -> dict:
    """Captures the current AI-generated state of a project as a plain dict."""
    return {
        "title": project.title,
        "description": project.description,
        "status": project.status,
        "analysis_json": project.analysis_json,
        "diagrams_json": project.diagrams_json,
        "api_spec_json": project.api_spec_json,
        "tech_stack_json": project.tech_stack_json,
        "planning_json": project.planning_json,
    }


def save_version(db: Session, project: Project, user_id: int, change_summary: str) -> ProjectVersion:
    last = (
        db.query(ProjectVersion)
        .filter(ProjectVersion.project_id == project.id)
        .order_by(ProjectVersion.version_number.desc())
        .first()
    )
    next_number = (last.version_number + 1) if last else 1

    version = ProjectVersion(
        project_id=project.id,
        version_number=next_number,
        snapshot_json=json.dumps(snapshot_fields(project)),
        created_by=user_id,
        change_summary=change_summary,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def diff_snapshots(old: dict, new: dict) -> dict:
    """Field-level diff between two snapshot dicts, with list-level detail for JSON fields."""
    changes = {}

    for key in ("title", "description", "status"):
        if old.get(key) != new.get(key):
            changes[key] = {"old": old.get(key), "new": new.get(key)}

    json_fields = ("analysis_json", "diagrams_json", "api_spec_json", "tech_stack_json", "planning_json")
    for key in json_fields:
        old_raw = old.get(key)
        new_raw = new.get(key)
        if old_raw == new_raw:
            continue

        try:
            old_data = json.loads(old_raw) if old_raw else {}
            new_data = json.loads(new_raw) if new_raw else {}
        except (json.JSONDecodeError, TypeError):
            changes[key] = {"changed": True, "old_present": old_raw is not None, "new_present": new_raw is not None}
            continue

        if key == "analysis_json":
            changes[key] = _diff_list_fields(old_data, new_data, [
                "objectives", "functional_requirements", "non_functional_requirements",
                "constraints", "assumptions", "target_users",
            ])
        else:
            changes[key] = {"changed": True, "old_present": old_raw is not None, "new_present": new_raw is not None}

    return changes


def _diff_list_fields(old_data: dict, new_data: dict, fields: list) -> dict:
    """For each list-type field, report which items were added and removed."""
    result = {}
    for field in fields:
        old_items = set(old_data.get(field, []))
        new_items = set(new_data.get(field, []))
        added = list(new_items - old_items)
        removed = list(old_items - new_items)
        if added or removed:
            result[field] = {"added": added, "removed": removed}
    return result