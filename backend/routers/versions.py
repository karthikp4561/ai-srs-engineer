from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json

from database import get_db
from models import Project, ProjectVersion
from schemas import VersionOut, VersionDiffOut
from collaboration_dependencies import require_viewer
from versioning_service import diff_snapshots

router = APIRouter(prefix="/projects/{project_id}/versions", tags=["Version Control"])


@router.get("/", response_model=List[VersionOut])
def list_versions(
    project: Project = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    return (
        db.query(ProjectVersion)
        .filter(ProjectVersion.project_id == project.id)
        .order_by(ProjectVersion.version_number.desc())
        .all()
    )


@router.get("/diff", response_model=VersionDiffOut)
def diff_versions(
    from_version: int,
    to_version: int,
    project: Project = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    v_from = (
        db.query(ProjectVersion)
        .filter(ProjectVersion.project_id == project.id, ProjectVersion.version_number == from_version)
        .first()
    )
    v_to = (
        db.query(ProjectVersion)
        .filter(ProjectVersion.project_id == project.id, ProjectVersion.version_number == to_version)
        .first()
    )
    if not v_from or not v_to:
        raise HTTPException(status_code=404, detail="One or both versions not found")

    old_snapshot = json.loads(v_from.snapshot_json)
    new_snapshot = json.loads(v_to.snapshot_json)
    changes = diff_snapshots(old_snapshot, new_snapshot)

    return VersionDiffOut(from_version=from_version, to_version=to_version, changes=changes)