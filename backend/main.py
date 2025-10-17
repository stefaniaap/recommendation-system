from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
from backend.database import get_db, init_db
from backend.core import UniversityRecommender
from pydantic import BaseModel
from backend.core2 import CourseRecommender
from backend.models import University, DegreeProgram, Course, Skill, CourseSkill

app = FastAPI(title="Academic Recommender API", version="1.0")

@app.on_event("startup")
def startup_event():
    try:
        init_db()
    except Exception as e:
        print(f"Error initializing DB: {e}")

@app.get("/similar/{univ_id}")
def get_similar(univ_id: int, top_n: int = 5, db: Session = Depends(get_db)):
    recommender = UniversityRecommender(db)
    similar_univs = recommender.find_similar_universities(univ_id, top_n=top_n)
    return {"target_university_id": univ_id, "similar_universities": similar_univs}

@app.get("/recommend/degrees/{university_id}")
def recommend_degrees(university_id: int, top_n: int = 5, db: Session = Depends(get_db)):
    recommender = UniversityRecommender(db)
    results = recommender.suggest_degrees_with_skills(university_id, top_n=top_n)
    return {"university_id": university_id, "recommended_degrees": results}

@app.get("/recommendations/university/{univ_id}")
def suggest_courses_for_university(univ_id: int, top_n: int = 10, db: Session = Depends(get_db)):
    recommender = CourseRecommender(db)
    result = recommender.suggest_courses(univ_id, top_n)
    return {"university_id": univ_id, "recommendations": result}

class RecommendRequest(BaseModel):
    university_id: int
    top_n: int = 10

@app.post("/recommendations")
def post_recommendations(payload: RecommendRequest, db: Session = Depends(get_db)):
    recommender = CourseRecommender(db)
    result = recommender.suggest_courses(payload.university_id, payload.top_n)
    return {"university_id": payload.university_id, "recommendations": result}

@app.get("/debug/db-counts")
def db_counts(db: Session = Depends(get_db)):
    return {
        "University": db.query(University).count(),
        "DegreeProgram": db.query(DegreeProgram).count(),
        "Course": db.query(Course).count(),
        "Skill": db.query(Skill).count(),
        "CourseSkill": db.query(CourseSkill).count(),
    }
