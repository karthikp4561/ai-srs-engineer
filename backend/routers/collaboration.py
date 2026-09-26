from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Project, ProjectCollaborator, User
from schemas import CollaboratorInvite, CollaboratorRoleUpdate, CollaboratorOut
from dependencies import get_current_user
from collaboration_dependencies import require_owner, require_viewer

router = APIRouter(prefix="/projects/{project_id}/collaborators", tags=["Collaboration"])


@router.get("/", response_model=List[CollaboratorOut])
def list_collaborators(
    project: Project = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(ProjectCollaborator, User)
        .join(User, ProjectCollaborator.user_id == User.id)
        .filter(ProjectCollaborator.project_id == project.id)
        .all()
    )
    return [
        CollaboratorOut(
            id=c.id, user_id=u.id, name=u.name, email=u.email,
            role=c.role, created_at=c.created_at
        )
        for c, u in rows
    ]


@router.post("/", response_model=CollaboratorOut, status_code=status.HTTP_201_CREATED)
def invite_collaborator(
    invite: CollaboratorInvite,
    project: Project = Depends(require_owner),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_user = db.query(User).filter(User.email == invite.email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="No user found with that email")
    if target_user.id == project.user_id:
        raise HTTPException(status_code=400, detail="This user already owns the project")

    existing = (
        db.query(ProjectCollaborator)
        .filter(ProjectCollaborator.project_id == project.id, ProjectCollaborator.user_id == target_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="This user is already a collaborator")

    collab = ProjectCollaborator(
        project_id=project.id, user_id=target_user.id,
        role=invite.role, invited_by=current_user.id,
    )
    db.add(collab)
    db.commit()
    db.refresh(collab)

    return CollaboratorOut(
        id=collab.id, user_id=target_user.id, name=target_user.name,
        email=target_user.email, role=collab.role, created_at=collab.created_at,
    )


@router.put("/{collaborator_id}", response_model=CollaboratorOut)
def update_collaborator_role(
    collaborator_id: int,
    update: CollaboratorRoleUpdate,
    project: Project = Depends(require_owner),
    db: Session = Depends(get_db),
):
    collab = (
        db.query(ProjectCollaborator)
        .filter(ProjectCollaborator.id == collaborator_id, ProjectCollaborator.project_id == project.id)
        .first()
    )
    if not collab:
        raise HTTPException(status_code=404, detail="Collaborator not found")

    collab.role = update.role
    db.commit()
    db.refresh(collab)

    user = db.query(User).filter(User.id == collab.user_id).first()
    return CollaboratorOut(
        id=collab.id, user_id=user.id, name=user.name,
        email=user.email, role=collab.role, created_at=collab.created_at,
    )


@router.delete("/{collaborator_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_collaborator(
    collaborator_id: int,
    project: Project = Depends(require_owner),
    db: Session = Depends(get_db),
):
    collab = (
        db.query(ProjectCollaborator)
        .filter(ProjectCollaborator.id == collaborator_id, ProjectCollaborator.project_id == project.id)
        .first()
    )
    if not collab:
        raise HTTPException(status_code=404, detail="Collaborator not found")

    db.delete(collab)
    db.commit()
    return None