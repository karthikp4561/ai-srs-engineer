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
    """Field-level diff between two snapshot dicts. Returns only fields that changed."""
    changes = {}
    for key in new:
        if key in ("title", "description", "status"):
            if old.get(key) != new.get(key):
                changes[key] = {"old": old.get(key), "new": new.get(key)}
        else:
            old_val = old.get(key)
            new_val = new.get(key)
            if old_val != new_val:
                changes[key] = {
                    "changed": True,
                    "old_present": old_val is not None,
                    "new_present": new_val is not None,
                }
    return changes