from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from urllib.parse import unquote
import logging

from backend.database import get_db
from backend.models import University
from backend.schemas import CourseRecommendationsResponse, DegreeProgramOut, UserPreferences
from backend.course_recommender_for_university import CourseRecommender as CourseRecommenderV2
from backend.degree_recommender_for_university import UniversityRecommender
from backend.student_recommender import CourseRecommender as CourseRecommenderV3

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/recommend/new_degree/{degree_name}",
    response_model=CourseRecommendationsResponse,
    summary="Recommend courses for a new degree across all universities."
)
async def recommend_courses_for_new_degree(
    degree_name: str = Path(..., description="URL-encoded name of the new degree."),
    top_n_courses: int = 10,
    db: Session = Depends(get_db)
):
    """
    Return recommended courses for a new degree based on similar degrees from other universities.
    Does not exclude existing courses since this is a completely new degree.
    """
    try:
        decoded_degree_name = unquote(degree_name).strip()
        recommender = CourseRecommenderV2(db)

        logger.info(f"Request for new degree_name='{decoded_degree_name}'")

        # 1️⃣ Gather all degree profiles from all universities
        all_univs = recommender.get_all_universities()
        all_profiles: List[Dict[str, Any]] = []
        for u in all_univs:
            profiles = recommender.build_degree_profiles(u.university_id)
            if profiles:
                all_profiles.extend(profiles)

        if not all_profiles:
            logger.warning("No degree profiles found in any university.")
            raise HTTPException(status_code=404, detail="No degree profiles found in any university.")

        # 2️⃣ Find similar degrees by matching normalized degree name
        similar_degrees = [
            p for p in all_profiles
            if recommender.normalize_name(p.get("degree_title")) == recommender.normalize_name(decoded_degree_name)
        ]

        # Fallback to all profiles if no exact match
        if not similar_degrees:
            logger.info("No exact degree name matches, using all profiles as similar degrees.")
            similar_degrees = all_profiles

        # 3️⃣ Aggregate all skills from similar degrees
        all_skills = set()
        for p in similar_degrees:
            all_skills.update(p.get("skills", []) or [])

        # 4️⃣ Suggest courses for the new degree
        try:
            result = recommender.suggest_courses_for_new_degree(
                similar_degrees=similar_degrees,
                target_skills=all_skills,
                top_n=top_n_courses
            )
        except Exception as e:
            logger.error(f"Error in suggest_courses_for_new_degree: {e}")
            raise HTTPException(status_code=500, detail="Course recommendation failed due to internal error.")

        # 5️⃣ Format final recommendations
        final_recommendations = [
            {
                "course_name": item.get("course_name", "Unknown"),
                "score": item.get("score", 0.0),
                "description": item.get("description", ""),
                "objectives": item.get("objectives", ""),
                "learning_outcomes": item.get("learning_outcomes", ""),
                "course_content": item.get("course_content", ""),
                "new_skills": sorted(item.get("new_skills", [])),
                "compatible_skills": sorted(item.get("compatible_skills", [])),
            }
            for item in result
            if isinstance(item, dict) and "course_name" in item
        ]

        # 6️⃣ Return final response
        return CourseRecommendationsResponse(
            university_id=-1,  # Not tied to a specific university
            program_id=-1,
            degree=decoded_degree_name,
            recommendations=final_recommendations
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in recommend_courses_for_new_degree: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.get(
    "/recommend/courses/{university_id}/{degree_name}",
    response_model=CourseRecommendationsResponse,
    summary="Recommend courses for a specific degree at a specific university."
)
async def recommend_courses_by_name_safe(
    university_id: int = Path(..., description="University ID"),
    degree_name: str = Path(..., description="URL-encoded name of the degree"),
    top_n_courses: int = 10,
    db: Session = Depends(get_db)
):
    """
    Return recommended courses for a specific degree, based on similar degree programs.
    """
    try:
        decoded_degree_name = unquote(degree_name).strip()
        recommender = CourseRecommenderV2(db)

        logger.info(f"Request for university_id={university_id}, degree_name='{decoded_degree_name}'")

        # 1️⃣ Gather all degree profiles
        all_univs = recommender.get_all_universities()
        all_profiles: List[Dict[str, Any]] = []
        for u in all_univs:
            profiles = recommender.build_degree_profiles(u.university_id)
            if profiles:
                all_profiles.extend(profiles)

        if not all_profiles:
            logger.warning("No degree profiles found in any university.")
            raise HTTPException(status_code=404, detail="No degree profiles found in any university.")

        # 2️⃣ Find representative profiles matching the degree name
        representative_profiles = [
            p for p in all_profiles
            if recommender.normalize_name(p.get("degree_title")) == recommender.normalize_name(decoded_degree_name)
        ]

        if not representative_profiles:
            logger.warning(f"Degree '{decoded_degree_name}' not found in any university.")
            raise HTTPException(
                status_code=404,
                detail=f"Degree '{decoded_degree_name}' not found in any university."
            )

        # 3️⃣ Create a synthetic target degree combining skills and courses
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

        # 4️⃣ Find similar degrees
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

        # 5️⃣ Suggest courses
        try:
            result = recommender.suggest_courses_for_degree(
                synthetic_target_degree,
                similar_degrees,
                top_n=top_n_courses
            )
        except Exception as e:
            logger.error(f"Error in suggest_courses_for_degree: {e}")
            raise HTTPException(status_code=500, detail="Course recommendation failed due to internal error.")

        # 6️⃣ Format final recommendations
        final_recommendations = [
            {
                "course_name": item.get("course_name", "Unknown"),
                "score": item.get("score", 0.0),
                "description": item.get("description", ""),
                "objectives": item.get("objectives", ""),
                "learning_outcomes": item.get("learning_outcomes", ""),
                "course_content": item.get("course_content", ""),
                "new_skills": sorted(item.get("new_skills", [])),
                "compatible_skills": sorted(item.get("compatible_skills", [])),
            }
            for item in result
            if isinstance(item, dict) and "course_name" in item
        ]

        # 7️⃣ Return response
        return CourseRecommendationsResponse(
            university_id=university_id,
            program_id=-1,
            degree=decoded_degree_name,
            recommendations=final_recommendations
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in recommend_courses_by_name_safe: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.get("/recommend/degrees/{university_id}", summary="Recommend degrees for a university.")
def recommend_degrees(university_id: int, top_n: int = 5, db: Session = Depends(get_db)):
    """
    Recommend top N degrees for a university based on recognized skills.
    """
    recommender = UniversityRecommender(db)
    results = recommender.suggest_degrees_with_skills(university_id, top_n=top_n)
    return {"university_id": university_id, "recommended_degrees": results}


@router.get("/recommendations/university/{univ_id}", summary="Suggest courses for a university.")
def suggest_courses_for_university(univ_id: int, top_n: int = 10, db: Session = Depends(get_db)):
    """
    Suggest top N courses for a specific university.
    """
    recommender = CourseRecommenderV2(db)
    result = recommender.suggest_courses(univ_id, top_n)
    return {"university_id": univ_id, "recommendations": result}


@router.post("/recommend/personalized", summary="Recommend personalized courses based on user preferences.")
def recommend_personalized(preferences: UserPreferences, db: Session = Depends(get_db)):
    """
    Recommend courses tailored to user preferences including target skills, language, country, and degree type.
    """
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
        logger.exception(f"Error in recommend_personalized: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
