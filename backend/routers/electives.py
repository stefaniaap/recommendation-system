from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.models import DegreeProgram, Skill
from backend.student_recommender import CourseRecommenderV4
from backend.schemas import ElectiveRecommendationRequest

router = APIRouter()

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