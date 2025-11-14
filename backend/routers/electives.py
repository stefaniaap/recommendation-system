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
    """
    Recommend elective courses for a specific degree program at a given university.

    Parameters:
    - univ_id (int): University ID.
    - payload (ElectiveRecommendationRequest): Request payload containing program_id, target skills, and top_n courses.
    - min_overlap_ratio (float): Minimum ratio of matching skills required for recommendation.
    - db (Session): SQLAlchemy database session (injected by FastAPI dependency).

    Returns:
    - JSON with success status, recommended electives with scores and matching skills, and meta information.
    """
    try:
        recommender = CourseRecommenderV4(db)

        # Fetch recommended electives using the recommender system
        result = recommender.recommend_electives_for_degree_enhanced(
            univ_id=univ_id,
            program_id=payload.program_id,
            target_skills=payload.target_skills,
            top_n=payload.top_n,
            min_overlap_ratio=min_overlap_ratio
        )

        # Handle empty or error response from recommender
        if not result or "message" in result:
            return {
                "success": False,
                "message": result.get("message", "No electives found for this program."),
                "recommended_electives": []
            }

        # Format recommended courses with scores and skills
        recommended_courses = [
            {
                "course_name": item.get("lesson_name", "Unknown"),
                "score": float(item.get("final_score", 0.0)),
                "skills": item.get("skills", []),
                "matching_skills": item.get("matching_skills", []),
                "missing_skills": item.get("missing_skills", []),
                "reason": item.get("reason", "")
            }
            for item in result.get("recommended_electives", [])
        ]

        return {
            "success": True,
            "recommended_electives": recommended_courses,
            "meta": result.get("meta", {})
        }

    except Exception as e:
        # Log the exception and return 500 Internal Server Error
        print(f"Error in recommend_electives endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.get(
    "/universities/{univ_id}/degrees/{program_id}/elective-skills",
    summary="Get skills from elective courses of a specific degree program"
)
def get_elective_skills_for_program(
    univ_id: int,
    program_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve all skills associated with elective courses of a specific degree program.

    Parameters:
    - univ_id (int): University ID.
    - program_id (int): Degree program ID.
    - db (Session): SQLAlchemy database session (injected by FastAPI dependency).

    Returns:
    - JSON containing a list of skills with skill_id and skill_name.
    """
    try:
        # Fetch the degree program for the university
        program = db.query(DegreeProgram).filter(
            DegreeProgram.program_id == program_id,
            DegreeProgram.university_id == univ_id
        ).first()

        if not program:
            raise HTTPException(
                status_code=404,
                detail="Degree program not found for this university."
            )

        # Filter only elective courses
        elective_courses = []
        for course in getattr(program, "courses", []) or []:
            mand_opt = getattr(course, "mand_opt_list", None)
            is_optional = False
            if isinstance(mand_opt, str) and "optional" in mand_opt.lower():
                is_optional = True
            elif isinstance(mand_opt, (list, tuple, set)):
                if any("optional" in str(v).lower() for v in mand_opt):
                    is_optional = True
            if is_optional:
                elective_courses.append(course)

        if not elective_courses:
            return {"skills": []}

        # Collect unique skill IDs from elective courses
        skill_ids = {
            cs.skill_id
            for course in elective_courses
            for cs in getattr(course, "skills", [])
            if hasattr(cs, "skill_id") and cs.skill_id
        }

        if not skill_ids:
            return {"skills": []}

        # Retrieve Skill objects from database and sort by name
        skills = db.query(Skill).filter(Skill.skill_id.in_(skill_ids)).order_by(Skill.skill_name.asc()).all()
        skill_list = [{"skill_id": s.skill_id, "skill_name": s.skill_name} for s in skills]

        return {"skills": skill_list}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_elective_skills_for_program: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
