from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
from backend.database import get_db, init_db
from backend.core import UniversityRecommender
from backend.core2 import CourseRecommender

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
