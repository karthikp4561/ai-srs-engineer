from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta

from database import get_db
from models import User, Project, AIUsageLog
from schemas import AdminUserOut, AdminProjectOut, AnalyticsSummary
from admin_dependencies import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=List[AdminUserOut])
def list_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.put("/users/{user_id}/toggle-active", response_model=AdminUserOut)
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    db.query(Project).filter(Project.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return {"detail": "User deleted"}


@router.get("/projects", response_model=List[AdminProjectOut])
def list_all_projects(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    rows = (
        db.query(Project, User.email)
        .join(User, Project.user_id == User.id)
        .order_by(Project.created_at.desc())
        .all()
    )
    return [
        AdminProjectOut(
            id=p.id, title=p.title, status=p.status,
            owner_email=email, created_at=p.created_at
        )
        for p, email in rows
    ]


@router.get("/analytics", response_model=AnalyticsSummary)
def get_analytics(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_projects = db.query(Project).count()

    status_rows = db.query(Project.status, func.count(Project.id)).group_by(Project.status).all()
    projects_by_status = {status: count for status, count in status_rows}

    action_rows = db.query(AIUsageLog.action, func.count(AIUsageLog.id)).group_by(AIUsageLog.action).all()
    ai_calls_by_action = {action: count for action, count in action_rows}

    week_ago = datetime.utcnow() - timedelta(days=7)
    ai_calls_last_7_days = db.query(AIUsageLog).filter(AIUsageLog.created_at >= week_ago).count()

    return AnalyticsSummary(
        total_users=total_users,
        total_projects=total_projects,
        active_users=active_users,
        projects_by_status=projects_by_status,
        ai_calls_by_action=ai_calls_by_action,
        ai_calls_last_7_days=ai_calls_last_7_days,
    )