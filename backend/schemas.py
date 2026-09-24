from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional, List
import re


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Name must be at least 2 characters long')
        if not re.match(r'^[A-Za-z\s]+$', v):
            raise ValueError('Name must contain only letters and spaces, no numbers or symbols')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProjectCreate(BaseModel):
    title: str
    description: str


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class AnalysisResult(BaseModel):
    objectives: List[str]
    scope: str
    target_users: List[str]
    functional_requirements: List[str]
    non_functional_requirements: List[str]
    constraints: List[str]
    assumptions: List[str]


class DiagramResult(BaseModel):
    use_case_diagram: str
    class_diagram: str
    er_diagram: str

class ApiEndpoint(BaseModel):
    method: str
    path: str
    description: str
    request_body: Optional[dict] = None
    response_body: Optional[dict] = None


class ApiSpecResult(BaseModel):
    endpoints: List[ApiEndpoint]

class TechRecommendation(BaseModel):
    technology: str
    reason: str


class TechStackResult(BaseModel):
    frontend: TechRecommendation
    backend: TechRecommendation
    database: TechRecommendation
    cloud_deployment: TechRecommendation
    third_party_integrations: List[TechRecommendation]


class ProjectPhase(BaseModel):
    name: str
    duration_weeks: int
    description: str


class Sprint(BaseModel):
    name: str
    duration_weeks: int
    goals: List[str]


class Milestone(BaseModel):
    name: str
    description: str


class Risk(BaseModel):
    risk: str
    impact: str
    mitigation: str


class PlanningResult(BaseModel):
    estimated_duration_weeks: int
    phases: List[ProjectPhase]
    sprints: List[Sprint]
    milestones: List[Milestone]
    risks: List[Risk]


class ProjectOut(BaseModel):
    id: int
    title: str
    description: str
    status: str
    analysis_json: Optional[str] = None
    diagrams_json: Optional[str] = None
    api_spec_json: Optional[str] = None
    tech_stack_json: Optional[str] = None
    planning_json: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AdminUserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AdminProjectOut(BaseModel):
    id: int
    title: str
    status: str
    owner_email: str
    created_at: datetime


class AnalyticsSummary(BaseModel):
    total_users: int
    total_projects: int
    active_users: int
    projects_by_status: dict
    ai_calls_by_action: dict
    ai_calls_last_7_days: int