from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db, engine, Base
from routers import auth
import models

from routers import auth, projects, admin

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Software Requirement Engineer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

@app.get("/")
def read_root():
    return {"message": "Backend is running 🚀"}

@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))
    return {"database": "connected ✅", "result": result.scalar()}

app.include_router(projects.router)

app.include_router(admin.router)