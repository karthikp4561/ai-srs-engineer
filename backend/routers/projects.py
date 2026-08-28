from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Project, User
from schemas import ProjectCreate, ProjectUpdate, ProjectOut
from dependencies import get_current_user

import json
from ai_service import analyze_project_description, generate_diagrams, generate_api_spec, generate_tech_stack, generate_project_plan

from fastapi.responses import StreamingResponse
from export_service import generate_pdf, generate_docx

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_project = Project(
        title=project.title,
        description=project.description,
        user_id=current_user.id,
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

@router.get("/", response_model=List[ProjectOut])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Project).filter(Project.user_id == current_user.id).order_by(Project.created_at.desc()).all()

@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    updates: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if updates.title is not None:
        project.title = updates.title
    if updates.description is not None:
        project.description = updates.description

    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()
    return None

@router.post("/{project_id}/analyze", response_model=ProjectOut)
def analyze_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        result = analyze_project_description(project.description)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {str(e)}")

    project.analysis_json = json.dumps(result)
    project.status = "analyzed"
    db.commit()
    db.refresh(project)
    return project

@router.post("/{project_id}/diagrams", response_model=ProjectOut)
def create_diagrams(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.analysis_json:
        raise HTTPException(status_code=400, detail="Project must be analyzed before generating diagrams")

    analysis = json.loads(project.analysis_json)

    try:
        diagrams = generate_diagrams(
            description=project.description,
            functional_requirements=analysis.get("functional_requirements", []),
            target_users=analysis.get("target_users", []),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Diagram generation failed: {str(e)}")

    project.diagrams_json = json.dumps(diagrams)
    db.commit()
    db.refresh(project)
    return project

@router.post("/{project_id}/api-spec", response_model=ProjectOut)
def create_api_spec(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.analysis_json:
        raise HTTPException(status_code=400, detail="Project must be analyzed before generating an API spec")

    analysis = json.loads(project.analysis_json)

    try:
        api_spec = generate_api_spec(
            description=project.description,
            functional_requirements=analysis.get("functional_requirements", []),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"API spec generation failed: {str(e)}")

    project.api_spec_json = json.dumps(api_spec)
    db.commit()
    db.refresh(project)
    return project

@router.post("/{project_id}/tech-stack", response_model=ProjectOut)
def create_tech_stack(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.analysis_json:
        raise HTTPException(status_code=400, detail="Project must be analyzed before generating tech stack recommendations")

    analysis = json.loads(project.analysis_json)

    try:
        tech_stack = generate_tech_stack(
            description=project.description,
            non_functional_requirements=analysis.get("non_functional_requirements", []),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Tech stack generation failed: {str(e)}")

    project.tech_stack_json = json.dumps(tech_stack)
    db.commit()
    db.refresh(project)
    return project

@router.post("/{project_id}/planning", response_model=ProjectOut)
def create_project_plan(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.analysis_json:
        raise HTTPException(status_code=400, detail="Project must be analyzed before generating a project plan")

    analysis = json.loads(project.analysis_json)

    try:
        plan = generate_project_plan(
            description=project.description,
            functional_requirements=analysis.get("functional_requirements", []),
            constraints=analysis.get("constraints", []),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Project plan generation failed: {str(e)}")

    project.planning_json = json.dumps(plan)
    db.commit()
    db.refresh(project)
    return project

@router.get("/{project_id}/export/pdf")
def export_pdf(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    buffer = generate_pdf(project)
    filename = f"{project.title.replace(' ', '_')}_SRS.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/{project_id}/export/docx")
def export_docx(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    buffer = generate_docx(project)
    filename = f"{project.title.replace(' ', '_')}_SRS.docx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )