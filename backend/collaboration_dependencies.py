from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Project, ProjectCollaborator, User
from dependencies import get_current_user

ROLE_RANK = {"viewer": 1, "editor": 2, "owner": 3}


def get_accessible_project(
    project_id: int,
    min_role: str = "viewer",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id == current_user.id:
        return project  # owner always has full access

    collab = (
        db.query(ProjectCollaborator)
        .filter(
            ProjectCollaborator.project_id == project_id,
            ProjectCollaborator.user_id == current_user.id,
        )
        .first()
    )
    if not collab or ROLE_RANK.get(collab.role, 0) < ROLE_RANK.get(min_role, 99):
        raise HTTPException(status_code=403, detail="You don't have access to this project")

    return project


def require_viewer(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Project:
    return get_accessible_project(project_id, "viewer", db, current_user)


def require_editor(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Project:
    return get_accessible_project(project_id, "editor", db, current_user)


def require_owner(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Project:
    return get_accessible_project(project_id, "owner", db, current_user)