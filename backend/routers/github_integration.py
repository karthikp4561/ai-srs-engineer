from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from database import get_db
from models import Project, GitHubConnection, User
from schemas import GitHubConnectRequest, GitHubConnectionOut, SyncResult
from collaboration_dependencies import require_owner, require_editor, require_viewer
from dependencies import get_current_user
from crypto_utils import encrypt_token, decrypt_token
from github_service import validate_repo_access, create_issue

router = APIRouter(prefix="/projects/{project_id}/github", tags=["GitHub Integration"])


@router.get("/", response_model=GitHubConnectionOut)
def get_connection(
    project: Project = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    conn = db.query(GitHubConnection).filter(GitHubConnection.project_id == project.id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="No GitHub connection for this project")
    synced = json.loads(conn.synced_issues_json) if conn.synced_issues_json else {}
    return GitHubConnectionOut(
        repo_owner=conn.repo_owner, repo_name=conn.repo_name,
        connected=True, created_at=conn.created_at,
        synced_issues=synced,
    )


@router.post("/connect", response_model=GitHubConnectionOut)
def connect_repo(
    payload: GitHubConnectRequest,
    project: Project = Depends(require_owner),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not validate_repo_access(payload.personal_access_token, payload.repo_owner, payload.repo_name):
        raise HTTPException(status_code=400, detail="Could not access that repository with the given token.")

    existing = db.query(GitHubConnection).filter(GitHubConnection.project_id == project.id).first()
    if existing:
        existing.encrypted_token = encrypt_token(payload.personal_access_token)
        existing.repo_owner = payload.repo_owner
        existing.repo_name = payload.repo_name
        db.commit()
        db.refresh(existing)
        conn = existing
    else:
        conn = GitHubConnection(
            project_id=project.id,
            encrypted_token=encrypt_token(payload.personal_access_token),
            repo_owner=payload.repo_owner,
            repo_name=payload.repo_name,
            connected_by=current_user.id,
        )
        db.add(conn)
        db.commit()
        db.refresh(conn)

    synced = json.loads(conn.synced_issues_json) if conn.synced_issues_json else {}
    return GitHubConnectionOut(
        repo_owner=conn.repo_owner, repo_name=conn.repo_name,
        connected=True, created_at=conn.created_at,
        synced_issues=synced,
    )


@router.delete("/")
def disconnect_repo(
    project: Project = Depends(require_owner),
    db: Session = Depends(get_db),
):
    conn = db.query(GitHubConnection).filter(GitHubConnection.project_id == project.id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="No GitHub connection for this project")
    db.delete(conn)
    db.commit()
    return {"detail": "Disconnected"}


@router.post("/sync-requirements", response_model=SyncResult)
def sync_requirements(
    project: Project = Depends(require_editor),
    db: Session = Depends(get_db),
):
    conn = db.query(GitHubConnection).filter(GitHubConnection.project_id == project.id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connect a GitHub repository first")

    if not project.analysis_json:
        raise HTTPException(status_code=400, detail="Project must be analyzed before syncing requirements")

    analysis = json.loads(project.analysis_json)
    requirements = analysis.get("functional_requirements", [])

    synced = json.loads(conn.synced_issues_json) if conn.synced_issues_json else {}
    token = decrypt_token(conn.encrypted_token)

    created = 0
    skipped = 0
    issue_urls = []

    for req in requirements:
        if req in synced:
            skipped += 1
            issue_urls.append(synced[req])
            continue
        try:
            issue = create_issue(
                token=token, owner=conn.repo_owner, repo=conn.repo_name,
                title=req[:80],
                body=f"**Auto-generated from ASRE**\n\nFunctional requirement:\n\n{req}\n\n---\nProject: {project.title}",
                labels=["requirement", "asre-generated"],
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"GitHub issue creation failed: {str(e)}")

        synced[req] = issue["html_url"]
        issue_urls.append(issue["html_url"])
        created += 1

    conn.synced_issues_json = json.dumps(synced)
    db.commit()

    return SyncResult(created=created, skipped=skipped, issue_urls=issue_urls, synced_issues=synced)