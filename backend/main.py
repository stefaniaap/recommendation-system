from fastapi import FastAPI, Depends, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from urllib.parse import unquote
from pydantic import BaseModel, Field

# Εισαγωγές για τη Βάση Δεδομένων, μοντέλα και Recommenders
from backend.database import get_db, init_db
from backend.models import University, DegreeProgram, Course, Skill, CourseSkill
from backend.core import UniversityRecommender 
from backend.core2 import CourseRecommender 

# =======================================================
# Pydantic Models για σωστή απόκριση (ΔΙΟΡΘΩΜΕΝΟ)
# =======================================================

class RecommendedCourse(BaseModel):
    course_name: str = Field(..., description="Όνομα του προτεινόμενου μαθήματος.")
    score: float = Field(..., description="Σκορ συνάφειας/σύστασης (0.0 έως 1.0).", ge=0.0, le=1.0)
    description: str = Field("", description="Αναλυτική περιγραφή του μαθήματος.")
    objectives: str = Field("", description="Στόχοι του μαθήματος.")
    learning_outcomes: str = Field("", description="Μαθησιακά αποτελέσματα του μαθήματος.")
    course_content: str = Field("", description="Περιεχόμενο του μαθήματος.")
    new_skills: List[str] = Field([], description="Νέες δεξιότητες που εισάγει το μάθημα.")
    compatible_skills: List[str] = Field([], description="Κοινές δεξιότητες με το πτυχίο.")


class CourseRecommendationsResponse(BaseModel):
    university_id: int
    program_id: int = Field(..., description="Το Program ID (-1 για προτεινόμενα νέα πτυχία)")
    degree: str
    recommendations: List[RecommendedCourse] 

# ✅ Προσθήκη για POST endpoint
class RecommendRequest(BaseModel):
    university_id: int
    top_n: int = 10


app = FastAPI(title="Academic Recommender API", version="1.0")

# =======================================================
# CORS Middleware
# =======================================================
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    try:
        init_db()
    except Exception as e:
        print(f"Error initializing DB: {e}")

# =======================================================
# 💡 ENDPOINT 1: Πρόταση Μαθημάτων ανά Πρόγραμμα (Program ID)
# =======================================================
@app.get("/recommend/courses/{university_id}", include_in_schema=False)
def recommend_courses_for_degree(
    university_id: int,
    program_id: int = Query(..., alias="program_id", description="Το ID του ακαδηδημαϊκού προγράμματος"),
    top_n_courses: int = 10,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """[Internal Use Only] Προτείνει μαθήματα (Courses) για ένα συγκεκριμένο Πρόγραμμα (Program ID)."""
    try:
        recommender = CourseRecommender(db)
        
        all_univs = recommender.get_all_universities()
        all_profiles: List[Dict[str, Any]] = []
        for u in all_univs:
            profiles = recommender.build_degree_profiles(u.university_id)
            if profiles:
                all_profiles.extend(profiles)
        
        if not all_profiles:
            raise HTTPException(status_code=404, detail="Δεν βρέθηκαν προφίλ πτυχίων σε κανένα πανεπιστήμιο.")
            
        target_profiles = recommender.build_degree_profiles(university_id)
        
        target_degree = next(
            (p for p in target_profiles
             if p.get("program_id") == program_id),
            None
        )

        if not target_degree:
            raise HTTPException(
                status_code=404,
                detail=f"Το Πρόγραμμα ID {program_id} δεν βρέθηκε στο Πανεπιστήμιο ID {university_id}."
            )
        
        degree_name = target_degree["degree_title"]
            
        similar_degrees = recommender.find_similar_degrees(
            target_degree,
            all_profiles,
            top_n=5
        )
        
        result = recommender.suggest_courses_for_degree(
            target_degree,
            similar_degrees,
            top_n=top_n_courses
        )
        
        final_recommendations = [
            {
                "course_name": item['course'], 
                "score": item['score'],
                "description": item.get('description', ''),
                "objectives": item.get('objectives', ''),
                "learning_outcomes": item.get('learning_outcomes', ''),
                "course_content": item.get('course_content', ''),
                "new_skills": item.get('new_skills', []),
                "compatible_skills": item.get('compatible_skills', []),
            }
            for item in result 
            if isinstance(item, dict) and 'course' in item and 'score' in item
        ]
        
        return {"university_id": university_id, "program_id": program_id, "degree": degree_name, "recommendations": final_recommendations}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error recommending courses for program {program_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

# =======================================================
# 💡 ENDPOINT 2: Πρόταση Μαθημάτων ανά Όνομα Πτυχίου (Frontend)
# =======================================================
@app.get(
    "/recommend/courses/{university_id}/{degree_name}",
    response_model=CourseRecommendationsResponse,
    summary="Προτείνει μαθήματα για ένα συγκεκριμένο Πτυχίο (Όνομα) σε ένα Πανεπιστήμιο."
)
async def recommend_courses_by_name(
    university_id: int = Path(..., description="Το ID του Πανεπιστημίου"),
    degree_name: str = Path(..., description="Το κωδικοποιημένο όνομα του Πτυχίου (URL-encoded)"),
    top_n_courses: int = 10,
    db: Session = Depends(get_db)
):
    decoded_degree_name = unquote(degree_name).strip()
    recommender = CourseRecommender(db)

    all_univs = recommender.get_all_universities()
    all_profiles: List[Dict[str, Any]] = []
    for u in all_univs:
        profiles = recommender.build_degree_profiles(u.university_id)
        if profiles:
            all_profiles.extend(profiles)
            
    if not all_profiles:
        raise HTTPException(status_code=404, detail="Δεν βρέθηκαν προφίλ πτυχίων σε κανένα πανεπιστήμιο.")
        
    representative_profiles = [
        p for p in all_profiles
        if recommender.normalize_name(p.get("degree_title")) == recommender.normalize_name(decoded_degree_name)
    ]
    
    if not representative_profiles:
        raise HTTPException(
            status_code=404,
            detail=f"Το Πτυχίο '{decoded_degree_name}' δεν βρέθηκε σε κανένα πανεπιστήμιο για ανάλυση."
        )

    degree_type = representative_profiles[0].get("degree_type", "N/A")
    all_skills = set()
    all_courses = set()
    
    for p in representative_profiles:
        all_skills.update(p.get("skills", []))
        all_courses.update(p.get("courses", []))
        
    synthetic_target_degree = {
        "university_id": university_id,
        "program_id": -1,
        "degree_title": decoded_degree_name,
        "degree_type": degree_type,
        "skills": list(all_skills),
        "courses": list(all_courses),
    }

    similar_degrees = recommender.find_similar_degrees(
        synthetic_target_degree,
        all_profiles,
        top_n=5
    )

    if not similar_degrees:
        return CourseRecommendationsResponse(
            university_id=university_id,
            program_id=-1,
            degree=decoded_degree_name,
            recommendations=[]
        )

    result = recommender.suggest_courses_for_degree(
        synthetic_target_degree,
        similar_degrees,
        top_n=top_n_courses
    )
    
    final_recommendations = [
        {
            "course_name": item['course'], 
            "score": item['score'],
            "description": item.get('description', ''),
            "objectives": item.get('objectives', ''),
            "learning_outcomes": item.get('learning_outcomes', ''),
            "course_content": item.get('course_content', ''),
            "new_skills": item.get('new_skills', []),
            "compatible_skills": item.get('compatible_skills', []),
        }
        for item in result 
        if isinstance(item, dict) and 'course' in item and 'score' in item
    ]
    
    return CourseRecommendationsResponse(
        university_id=university_id,
        program_id=-1,
        degree=decoded_degree_name,
        recommendations=final_recommendations
    )

# =======================================================
# ΛΟΙΠΑ ENDPOINTS (Παραμένουν ως είχαν)
# =======================================================

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

# ✅ Προσθήκη POST endpoint από 1η έκδοση
@app.post("/recommendations")
def post_recommendations(payload: RecommendRequest, db: Session = Depends(get_db)):
    recommender = CourseRecommender(db)
    result = recommender.suggest_courses(payload.university_id, payload.top_n)
    return {"university_id": payload.university_id, "recommendations": result}

# ✅ Προσθήκη debug endpoint από 1η έκδοση
@app.get("/debug/db-counts")
def db_counts(db: Session = Depends(get_db)):
    return {
        "University": db.query(University).count(),
        "DegreeProgram": db.query(DegreeProgram).count(),
        "Course": db.query(Course).count(),
        "Skill": db.query(Skill).count(),
        "CourseSkill": db.query(CourseSkill).count(),
    }

@app.get("/universities")
def get_all_universities(db: Session = Depends(get_db)):
    universities = db.query(University).order_by(University.university_name).all()
    return [
        {"university_id": u.university_id, "university_name": u.university_name, "country": u.country}
        for u in universities
    ]

@app.get("/metrics/{university_id}")
def get_university_metrics(university_id: int, db: Session = Depends(get_db)):
    university = db.query(University).filter_by(university_id=university_id).first()

    if not university:
        raise HTTPException(status_code=404, detail="University not found")

    total_programs = len(university.programs)
    
    unique_skills_count = (
        db.query(func.count(distinct(CourseSkill.skill_id)))
        .filter(CourseSkill.course_id.in_([c.course_id for c in university.courses]))
        .scalar()
    )

    recognized_skills_final = unique_skills_count if unique_skills_count is not None else 0
    
    return {
        "university_id": university_id,
        "total_programs": total_programs,
        "recognized_skills": recognized_skills_final
    }
