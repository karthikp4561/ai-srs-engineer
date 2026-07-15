from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

app = FastAPI(title="AI Software Requirement Engineer")

@app.get("/")
def read_root():
    return {"message": "Backend is running 🚀"}

@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))
    return {"database": "connected ✅", "result": result.scalar()}