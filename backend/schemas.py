from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

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

class ProjectOut(BaseModel):
    id: int
    title: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True