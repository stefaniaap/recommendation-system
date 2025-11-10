from fastapi import FastAPI, Depends, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, distinct, or_
from urllib.parse import unquote
from pydantic import BaseModel, Field
from fastapi import APIRouter, Query, Depends


# Εισαγωγές για τη Βάση Δεδομένων, μοντέλα και Recommenders
from backend.database import get_db, init_db
from backend.models import University, DegreeProgram, Course, Skill, CourseSkill, text
from backend.core import UniversityRecommender
from backend.core2 import CourseRecommender as CourseRecommenderV2
from backend.core3 import CourseRecommender as CourseRecommenderV3

from collections import defaultdict
from fastapi import HTTPException


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

# =======================================================
# Pydantic Models για σωστή απόκριση
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


class RecommendRequest(BaseModel):
    university_id: int
    top_n: int = 10


# Pydantic Models για την έξοδο της Αναζήτησης
class UniversityBase(BaseModel):
    university_id: int
    university_name: str
    country: str
   
    class Config:
        orm_mode = True


class DegreeProgramSearch(BaseModel):
    program_id: int
    degree_type: str
    # Σημείωση: Το degree_titles είναι JSON.
    degree_titles: Optional[dict]
    language: Optional[str]
    # Εισαγωγή του University
    university: UniversityBase
   
    class Config:
        orm_mode = True


class CourseSearch(BaseModel):
    course_id: int
    lesson_name: str
    language: Optional[str]
    semester_label: Optional[str]
    description: Optional[str]
    # Εισαγωγή του University
    university: UniversityBase
   
    class Config:
        orm_mode = True


# Pydantic Model για τα αποτελέσματα της Αναζήτησης
class SearchResult(BaseModel):
    degree_programs: List[DegreeProgramSearch]
    courses: List[CourseSearch]






@app.on_event("startup")
def startup_event():
    try:
        init_db()
    except Exception as e:
        print(f"Error initializing DB: {e}")


# =========================================================================
## 🔍 Endpoints Αναζήτησης και Δεξιοτήτων
# =========================================================================


# 1. Endpoint: Dropdown Skills με Ομαδοποίηση (βάσει categories)



@app.get("/skills/grouped-by-categories", response_model=Dict[str, List[Dict[str, Any]]], summary="Ομαδοποιημένες Δεξιότητες βάσει Categories")
def get_grouped_skills_by_categories(db: Session = Depends(get_db)):
    """
    Επιστρέφει όλα τα skills, ομαδοποιημένα με βάση τις κατηγορίες που δηλώνονται στα CourseSkill.categories.
    Αν ένα skill ανήκει σε πολλές κατηγορίες, θα εμφανίζεται σε όλες.
    Αφαιρούνται διπλές δεξιότητες με ίδιο όνομα μέσα στην ίδια κατηγορία.
    """
    try:
        links = db.query(CourseSkill).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    grouped_skills = defaultdict(list)

    for link in links:
        skill = db.query(Skill).filter(Skill.skill_id == link.skill_id).first()
        if not skill:
            continue

        skill_name = skill.skill_name.strip()

        # Αν υπάρχουν categories, τοποθετούμε το skill σε κάθε μία
        if link.categories and isinstance(link.categories, list) and len(link.categories) > 0:
            for cat in link.categories:
                # Ελέγχουμε αν υπάρχει ήδη δεξιότητα με το ίδιο όνομα (case-insensitive)
                if not any(s["name"].lower() == skill_name.lower() for s in grouped_skills[cat]):
                    grouped_skills[cat].append({
                        "id": skill.skill_id,
                        "name": skill_name
                    })
        else:
            cat = "Άλλες/Χωρίς Κατηγορία"
            if not any(s["name"].lower() == skill_name.lower() for s in grouped_skills[cat]):
                grouped_skills[cat].append({
                    "id": skill.skill_id,
                    "name": skill_name
                })

    # Ταξινόμηση δεξιοτήτων αλφαβητικά μέσα σε κάθε κατηγορία
    for cat in grouped_skills:
        grouped_skills[cat] = sorted(grouped_skills[cat], key=lambda x: x["name"].lower())

    # Ταξινόμηση κατηγοριών αλφαβητικά
    grouped_sorted = dict(sorted(grouped_skills.items(), key=lambda x: x[0].lower()))

    return grouped_sorted



# 2. Endpoint: Αναζήτηση Προγραμμάτων και Μαθημάτων με Φίλτρα



@app.get("/search", summary="Αναζήτηση Προγραμμάτων Σπουδών και Μαθημάτων")
def search_academic_data(
    skill_names: List[str] = Query(..., description="Λίστα με ονόματα δεξιοτήτων"),
    degree_type: Optional[str] = Query(None, description="Τύπος Πτυχίου (BSc, MSc, PhD, Other)"),
    country: Optional[str] = Query(None, description="Χώρα του Πανεπιστημίου"),
    language: Optional[str] = Query(None, description="Γλώσσα Διδασκαλίας"),
    db: Session = Depends(get_db)
):
    # --- Μετατροπή ονομάτων δεξιοτήτων σε IDs ---
    skill_ids = [
        s.skill_id
        for s in db.query(Skill).filter(Skill.skill_name.in_(skill_names)).all()
    ]
    
    # Αν δεν βρέθηκαν skill_ids, αγνοούμε το φίλτρο
    if not skill_ids:
        skill_ids = None

    # --- Αναζήτηση Προγραμμάτων ---
    program_query = db.query(DegreeProgram).options(joinedload(DegreeProgram.university))
    
    if degree_type:
        program_query = program_query.filter(DegreeProgram.degree_type.ilike(degree_type))
    
    if country:
        program_query = program_query.join(University).filter(University.country.ilike(country))
    
    if language:
        program_query = program_query.filter(DegreeProgram.language.ilike(f"%{language}%"))
    
    if skill_ids:
        programs_with_courses = (
            db.query(Course.program_id)
            .join(CourseSkill)
            .filter(CourseSkill.skill_id.in_(skill_ids))
            .distinct()
        )
        program_query = program_query.filter(DegreeProgram.program_id.in_(programs_with_courses))
    
    programs_results = program_query.all()

    # --- Αναζήτηση Μαθημάτων ---
    course_query = db.query(Course).options(joinedload(Course.university))
    
    if country:
        course_query = course_query.join(University).filter(University.country.ilike(country))
    
    if language:
        course_query = course_query.filter(Course.language.ilike(f"%{language}%"))
    
    if skill_ids:
        course_query = course_query.join(CourseSkill).filter(CourseSkill.skill_id.in_(skill_ids))
    
    courses_results = course_query.distinct().all()

    return {
        "degree_programs": programs_results,
        "courses": courses_results
    }



# =======================================================
## 💡 Endpoints Συστάσεων (Recommenders)
# =======================================================


# 💡 ENDPOINT 1: Πρόταση Μαθημάτων ανά Πρόγραμμα (Program ID)
@app.get("/recommend/courses/{university_id}", include_in_schema=False)
def recommend_courses_for_degree(
    university_id: int,
    program_id: int = Query(..., alias="program_id", description="Το ID του ακαδηδημαϊκού προγράμματος"),
    top_n_courses: int = 10,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """[Internal Use Only] Προτείνει μαθήματα (Courses) για ένα συγκεκριμένο Πρόγραμμα (Program ID)."""
    try:
        recommender = CourseRecommenderV2(db)
       
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


# 💡 ENDPOINT 2: Πρόταση Μαθημάτων ανά Όνομα Πτυχίου (Frontend)
import logging
from urllib.parse import unquote
from fastapi import HTTPException, Path, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

logger = logging.getLogger(__name__)

@app.get(
    "/recommend/courses/{university_id}/{degree_name}",
    response_model=CourseRecommendationsResponse,
    summary="Προτείνει μαθήματα για ένα συγκεκριμένο Πτυχίο (Όνομα) σε ένα Πανεπιστήμιο."
)
async def recommend_courses_by_name_safe(
    university_id: int = Path(..., description="Το ID του Πανεπιστημίου"),
    degree_name: str = Path(..., description="Το κωδικοποιημένο όνομα του Πτυχίου (URL-encoded)"),
    top_n_courses: int = 10,
    db: Session = Depends(get_db)
):
    try:
        decoded_degree_name = unquote(degree_name).strip()
        recommender = CourseRecommenderV2(db)

        logger.info(f"Request for university_id={university_id}, degree_name='{decoded_degree_name}'")

        # Συλλογή όλων των προφίλ
        all_univs = recommender.get_all_universities()
        all_profiles: List[Dict[str, Any]] = []
        for u in all_univs:
            profiles = recommender.build_degree_profiles(u.university_id)
            if profiles:
                all_profiles.extend(profiles)

        if not all_profiles:
            logger.warning("No degree profiles found in any university.")
            raise HTTPException(status_code=404, detail="Δεν βρέθηκαν προφίλ πτυχίων σε κανένα πανεπιστήμιο.")

        # Βρες τα profiles που ταιριάζουν με το όνομα πτυχίου
        representative_profiles = [
            p for p in all_profiles
            if recommender.normalize_name(p.get("degree_title")) == recommender.normalize_name(decoded_degree_name)
        ]

        if not representative_profiles:
            logger.warning(f"Degree '{decoded_degree_name}' not found in any university.")
            raise HTTPException(
                status_code=404,
                detail=f"Το Πτυχίο '{decoded_degree_name}' δεν βρέθηκε σε κανένα πανεπιστήμιο για ανάλυση."
            )

        # Δημιουργία συνθετικού target degree
        degree_type = representative_profiles[0].get("degree_type", "N/A")
        all_skills = set()
        all_courses = set()
        for p in representative_profiles:
            all_skills.update(p.get("skills", []) or [])
            all_courses.update(p.get("courses", []) or [])

        synthetic_target_degree = {
            "university_id": university_id,
            "program_id": -1,
            "degree_title": decoded_degree_name,
            "degree_type": degree_type,
            "skills": list(all_skills),
            "courses": list(all_courses),
        }

        # Βρες παρόμοια πτυχία
        similar_degrees = recommender.find_similar_degrees(
            synthetic_target_degree,
            all_profiles,
            top_n=5
        )

        if not similar_degrees:
            logger.info("No similar degrees found. Returning empty recommendations.")
            return CourseRecommendationsResponse(
                university_id=university_id,
                program_id=-1,
                degree=decoded_degree_name,
                recommendations=[]
            )

        # Προτεινόμενα μαθήματα με ασφαλή handling
        result = []
        try:
            result = recommender.suggest_courses_for_degree(
                synthetic_target_degree,
                similar_degrees,
                top_n=top_n_courses
            )
        except Exception as e:
            logger.error(f"Error in suggest_courses_for_degree: {e}")
            result = [{"info": "Η σύσταση απέτυχε λόγω εσωτερικού σφάλματος."}]

        # Φιλτράρισμα μόνο σωστών αντικειμένων
        final_recommendations = [
            {
                "course_name": item.get('course', 'Unknown'),
                "score": item.get('score', 0.0),
                "description": item.get('description', ''),
                "objectives": item.get('objectives', ''),
                "learning_outcomes": item.get('learning_outcomes', ''),
                "course_content": item.get('course_content', ''),
                "new_skills": sorted(item.get('new_skills', [])),
                "compatible_skills": sorted(item.get('compatible_skills', [])),
            }
            for item in result
            if isinstance(item, dict) and ('course' in item or 'info' in item)
        ]

        return CourseRecommendationsResponse(
            university_id=university_id,
            program_id=-1,
            degree=decoded_degree_name,
            recommendations=final_recommendations
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Unexpected error in recommend_courses_by_name_safe: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


# =======================================================
## 📊 Λοιπά Endpoints Πληροφοριών (Συμπεριλαμβανομένων των ΝΕΩΝ Φίλτρων)
# =======================================================


### ⚙️ Endpoints Φίλτρων


@app.get("/filters/degree-types", response_model=List[str], summary="Επιστρέφει όλους τους μοναδικούς Τύπους Πτυχίου.")
def get_unique_degree_types(db: Session = Depends(get_db)):
    """
    Εξάγει μοναδικούς τύπους πτυχίου (BSc, MSc, PhD, Other) για χρήση σε φίλτρα.
    """
    results = db.query(distinct(DegreeProgram.degree_type)).all()
    return [r[0] for r in results if r[0]]


@app.get("/filters/countries", response_model=List[str], summary="Επιστρέφει όλες τις μοναδικές Χώρες Πανεπιστημίων.")
def get_unique_countries(db: Session = Depends(get_db)):
    """
    Εξάγει μοναδικές χώρες από τον πίνακα University για χρήση σε φίλτρα.
    """
    results = (
        db.query(distinct(University.country))
        .order_by(University.country)
        .all()
    )
    return [r[0] for r in results if r[0]]


@app.get("/filters/languages", response_model=List[str], summary="Επιστρέφει όλες τις μοναδικές Γλώσσες Μαθημάτων/Προγραμμάτων.")
def get_unique_languages(db: Session = Depends(get_db)):
    """
    Εξάγει μοναδικές γλώσσες από τους πίνακες DegreeProgram και Course για χρήση σε φίλτρα.
    """
    # 1. Γλώσσες από DegreeProgram
    program_languages = (
        db.query(DegreeProgram.language)
        .filter(DegreeProgram.language.isnot(None))
        .distinct()
    )
   
    # 2. Γλώσσες από Course
    course_languages = (
        db.query(Course.language)
        .filter(Course.language.isnot(None))
        .distinct()
    )
   
    combined_languages = set()
    # Εφαρμόζουμε Union για να πάρουμε μοναδικές γλώσσες και από τους δύο πίνακες
    for lang_tuple in program_languages.union(course_languages).all():
        if lang_tuple[0]:
            # Χειρισμός πολλαπλών γλωσσών σε ένα πεδίο (π.χ. "English, Greek")
            parts = [part.strip() for part in lang_tuple[0].split(',') if part.strip()]
            combined_languages.update(parts)


    return sorted(list(combined_languages))


### ℹ️ Γενικές Πληροφορίες


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
    recommender = CourseRecommenderV2(db)
    result = recommender.suggest_courses(univ_id, top_n)
    return {"university_id": univ_id, "recommendations": result}


@app.post("/recommendations")
def post_recommendations(payload: RecommendRequest, db: Session = Depends(get_db)):
    recommender = CourseRecommenderV2(db)
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


class UserPreferences(BaseModel):
    target_skills: List[str]
    language: Optional[str] = None
    country: Optional[str] = None
    degree_type: Optional[str] = None
    top_n: int = 10

@app.post("/recommend/personalized")
def recommend_personalized(preferences: UserPreferences, db: Session = Depends(get_db)):
    try:
        recommender = CourseRecommenderV3(db)
        results = recommender.recommend_personalized(
            target_skills=preferences.target_skills,
            language=preferences.language,
            country=preferences.country,
            degree_type=preferences.degree_type,
            top_n=preferences.top_n
        )
        return results
    except Exception as e:
        # Εκτυπώνουμε το error για debugging
        print(f"Error in recommend_personalized: {e}")
        # Επιστρέφουμε friendly error στο frontend
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.get("/degree-programs/{university_id}", summary="Λίστα Προγραμμάτων ανά Πανεπιστήμιο")
def get_degree_programs_by_university(university_id: int, db: Session = Depends(get_db)):
    programs = (
        db.query(DegreeProgram)
        .filter(DegreeProgram.university_id == university_id)
        .order_by(DegreeProgram.degree_type)
        .all()
    )
    return [
        {
            "program_id": p.program_id,
            "degree_title": p.degree_titles.get("en", p.degree_titles.get("el", "")) if isinstance(p.degree_titles, dict) else p.degree_type,
            "degree_type": p.degree_type,
        }
        for p in programs
    ]

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from backend.models import University
from backend.database import get_db
from pydantic import BaseModel

class DegreeProgramOut(BaseModel):
    program_id: int
    degree_type: str
    degree_titles: list | None
    language: str | None
    duration_semesters: str | None
    total_ects: str | None

    class Config:
        orm_mode = True

@app.get("/universities/{univ_id}/degrees", response_model=List[DegreeProgramOut])
def get_degree_programs(univ_id: int, db: Session = Depends(get_db)):
    university = db.query(University).filter(University.university_id == univ_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")

    return university.programs
from fastapi import Body

class ElectiveRecommendationRequest(BaseModel):
    program_id: int = Field(..., description="Το ID του πτυχίου για το οποίο ζητάμε προτάσεις μαθημάτων επιλογής")
    target_skills: List[str] = Field(..., description="Δεξιότητες που θέλει να αναπτύξει ο χρήστης")
    top_n: int = Field(10, description="Πόσα κορυφαία μαθήματα να επιστραφούν")

# ==============================
# Endpoint για προτεινόμενα electives
# ==============================
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from backend.models import University
from backend.database import get_db
from pydantic import BaseModel

class DegreeProgramOut(BaseModel):
    program_id: int
    degree_type: str
    degree_titles: list | None
    language: str | None
    duration_semesters: str | None
    total_ects: str | None

    class Config:
        orm_mode = True

@app.get("/universities/{univ_id}/degrees", response_model=List[DegreeProgramOut])
def get_degree_programs(univ_id: int, db: Session = Depends(get_db)):
    university = db.query(University).filter(University.university_id == univ_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")

    return university.programs
from fastapi import Body

class ElectiveRecommendationRequest(BaseModel):
    program_id: int = Field(..., description="Το ID του πτυχίου για το οποίο ζητάμε προτάσεις μαθημάτων επιλογής")
    target_skills: List[str] = Field(..., description="Δεξιότητες που θέλει να αναπτύξει ο χρήστης")
    top_n: int = Field(10, description="Πόσα κορυφαία μαθήματα να επιστραφούν")

# ==============================
# Endpoint για προτεινόμενα electives
# ==============================
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from backend.core3 import CourseRecommenderV4
from backend.database import get_db
from backend.models import DegreeProgram, Skill

router = APIRouter()


class ElectiveRecommendationRequest(BaseModel):
    program_id: int
    target_skills: List[str]
    top_n: int = 10


@router.post("/universities/{univ_id}/degrees/electives")
def recommend_electives(
    univ_id: int,
    payload: ElectiveRecommendationRequest,
    min_overlap_ratio: float = 0.0,
    db: Session = Depends(get_db)
):
    try:
        recommender = CourseRecommenderV4(db)

        # Κλήση στο recommender
        result = recommender.recommend_electives_for_degree_enhanced(
            univ_id=univ_id,
            program_id=payload.program_id,
            target_skills=payload.target_skills,
            top_n=payload.top_n,
            min_overlap_ratio=min_overlap_ratio
        )

        # Αν δεν υπάρχει αποτέλεσμα ή επιστρέφει μήνυμα σφάλματος
        if not result or "message" in result:
            return {
                "success": False,
                "message": result.get("message", "Δεν βρέθηκαν διαθέσιμα electives για αυτό το πρόγραμμα."),
                "recommended_electives": []
            }

        # Διασφάλιση ότι κάθε course έχει score
        recommended_courses = []
        for item in result.get("recommended_electives", []):
            recommended_courses.append({
                "course_name": item.get("lesson_name", "Unknown"),
                "score": float(item.get("final_score", 0.0)),
                "skills": item.get("skills", []),
                "matching_skills": item.get("matching_skills", []),
                "missing_skills": item.get("missing_skills", []),
                "reason": item.get("reason", "")
            })

        return {
            "success": True,
            "recommended_electives": recommended_courses,
            "meta": result.get("meta", {})
        }

    except Exception as e:
        # Logging για debugging
        print(f"Error in recommend_electives endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


# ==============================
# Endpoint για δεξιότητες από μαθήματα επιλογής συγκεκριμένου πτυχίου


@router.get(
    "/universities/{univ_id}/degrees/{program_id}/elective-skills",
    summary="Δεξιότητες από μαθήματα επιλογής συγκεκριμένου πτυχίου"
)
def get_elective_skills_for_program(
    univ_id: int,
    program_id: int,
    db: Session = Depends(get_db)
):
    try:
        # --- Βρες το πρόγραμμα σπουδών για το πανεπιστήμιο ---
        program = db.query(DegreeProgram).filter(
            DegreeProgram.program_id == program_id,
            DegreeProgram.university_id == univ_id
        ).first()

        if not program:
            raise HTTPException(
                status_code=404,
                detail="Δεν βρέθηκε το πρόγραμμα σπουδών για αυτό το πανεπιστήμιο."
            )

        # --- Φιλτράρισμα μαθημάτων επιλογής ---
        elective_courses = []
        for c in getattr(program, "courses", []) or []:
            mand_opt = getattr(c, "mand_opt_list", None)
            is_optional = False
            if isinstance(mand_opt, str) and "optional" in mand_opt.lower():
                is_optional = True
            elif isinstance(mand_opt, (list, tuple, set)):
                for v in mand_opt:
                    if "optional" in str(v).lower():
                        is_optional = True
                        break
            if is_optional:
                elective_courses.append(c)

        if not elective_courses:
            return {"skills": []}

        # --- Συλλογή skill_ids ---
        skill_ids = set()
        for course in elective_courses:
            for cs in getattr(course, "skills", []):
                if hasattr(cs, "skill_id") and cs.skill_id:
                    skill_ids.add(cs.skill_id)

        if not skill_ids:
            return {"skills": []}

        # --- Βρες τα skill objects ---
        skills = db.query(Skill).filter(Skill.skill_id.in_(skill_ids)).order_by(Skill.skill_name.asc()).all()
        skill_list = [{"skill_id": s.skill_id, "skill_name": s.skill_name} for s in skills]

        return {"skills": skill_list}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in get_elective_skills_for_program: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# =======================================================
# ✅ ΕΝΣΩΜΑΤΩΣΗ ΤΟΥ ROUTER ΣΤΟ ΚΥΡΙΟ APP
# =======================================================
# app.include_router(router)  # Βεβαιώσου ότι το έχεις κάνει στο main app

# ✅ ΕΝΣΩΜΑΤΩΣΗ ΤΟΥ ROUTER ΣΤΟ ΚΥΡΙΟ APP
# =======================================================
app.include_router(router)
