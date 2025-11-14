from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import distinct, func
from collections import defaultdict

from backend.database import get_db
from backend.models import DegreeProgram, University, Course, Skill, CourseSkill
from backend.schemas import CourseRecommendationsResponse, DegreeProgramOut
from backend.course_recommender_for_university import CourseRecommender as CourseRecommenderV2
from backend.degree_recommender_for_university import UniversityRecommender

router = APIRouter()


@router.get("/filters/degree-types", response_model=List[str], summary="Επιστρέφει όλους τους μοναδικούς Τύπους Πτυχίου.")
def get_unique_degree_types(db: Session = Depends(get_db)):
    """
    Εξάγει μοναδικούς τύπους πτυχίου (BSc, MSc, PhD, Other) για χρήση σε φίλτρα.
    """
    results = db.query(distinct(DegreeProgram.degree_type)).all()
    return [r[0] for r in results if r[0]]


@router.get("/filters/countries", response_model=List[str], summary="Επιστρέφει όλες τις μοναδικές Χώρες Πανεπιστημίων.")
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


@router.get("/filters/languages", response_model=List[str], summary="Επιστρέφει όλες τις μοναδικές Γλώσσες Μαθημάτων/Προγραμμάτων.")
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


@router.get("/universities")
def get_all_universities(db: Session = Depends(get_db)):
    universities = db.query(University).order_by(University.university_name).all()
    return [
        {"university_id": u.university_id, "university_name": u.university_name, "country": u.country}
        for u in universities
    ]

@router.get("/universities/{univ_id}/degrees", response_model=List[DegreeProgramOut])
def get_degree_programs(univ_id: int, db: Session = Depends(get_db)):
    university = db.query(University).filter(University.university_id == univ_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")

    return university.programs



@router.get("/metrics/{university_id}")
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


@router.get("/skills/grouped-by-categories", response_model=Dict[str, List[Dict[str, Any]]], summary="Ομαδοποιημένες Δεξιότητες βάσει Categories")
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