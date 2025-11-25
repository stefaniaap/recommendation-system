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
from backend.models import Course

logger = logging.getLogger(__name__)
router = APIRouter()

# backend/student_recommender.py (μέσα στην κλάση CourseRecommender)

from sqlalchemy.orm import Session
from collections import Counter

class CourseRecommender:


    def __init__(self, db: Session):
        self.db = db

# ---------------------------
# Νέα μέθοδος: History-based recommendations
# ---------------------------
    def recommend_based_on_history(
        self,
        user_id: int,
        top_n: int = 10
    ):
        """
        Recommend courses based on the user's past selections/interactions.
        Combines personalized preferences with history-aware scoring.
        """
        # 1️⃣ Συλλογή ιστορικού χρήστη
        from backend.models import UserInteraction  # assume table exists
        user_history = self.db.query(UserInteraction)\
                            .filter(UserInteraction.user_id == user_id,
                                    UserInteraction.course_name != None)\
                            .all()
        if not user_history:
            return []  # Δεν υπάρχει ιστορικό, fallback σε default personalized

        # 2️⃣ Μετράμε τις πιο συχνές επιλογές του χρήστη
        course_counter = Counter([h.course_name for h in user_history])
        most_selected_courses = [c for c, _ in course_counter.most_common(50)]  # top 50 history

        # 3️⃣ Ανάκτηση όλων διαθέσιμων μαθημάτων
        all_courses = self.db.query(Course).all()  # assume Course model exists
        course_scores = []

        # 4️⃣ Σκοράρισμα με βάση similarity με ιστορικό
        for course in all_courses:
            score = 0.0

            # bonus αν το course είναι ίδιο με προηγούμενες επιλογές
            if course.lesson_name in most_selected_courses:
                score += 1.0

            # bonus αν τα skills του course εμφανίζονται συχνά στο ιστορικό
            user_skills = []
            for h in user_history:
                user_skills.extend(getattr(h, "skills", []))  # προσαρμόστε αν χρειάζεται
            common_skills = set(getattr(course, "skills", [])) & set(user_skills)
            score += 0.5 * len(common_skills)

            # τελικό score μπορεί να προσαρμοστεί με TF-IDF ή collaborative filtering
            course_scores.append({"course_name": course.lesson_name, "score": score})

        # 5️⃣ Ταξινόμηση και επιλογή top N
        top_recommendations = sorted(course_scores, key=lambda x: x["score"], reverse=True)[:top_n]

        # 6️⃣ Προσθήκη σημείωσης “based on your past selections”
        for c in top_recommendations:
            c["reason"] = "Based on your past selections"

        return top_recommendations

@router.get("/recommend/personalized/history/{user_id}")
def recommend_personalized_history(user_id: int, top_n: int = 10, db: Session = Depends(get_db)):
    recommender = CourseRecommenderV3(db)
    results = recommender.recommend_based_on_history(user_id, top_n)
    return {"user_id": user_id, "recommendations": results}


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

        
from pydantic import BaseModel
from backend.models import UserInteraction
from backend.models import DegreeProgram, Course, UserInteraction

class InteractionIn(BaseModel):
    user_id: int
    course_name: str
    interest_score: float = 1.0  # default 1.0, αυξάνεται αν enrolled/confirmed


# ---------------------------
# Endpoint για αποθήκευση interaction
# ---------------------------
@router.post("/interactions/add")
def add_interaction(data: InteractionIn, db: Session = Depends(get_db)):

    course = db.query(Course).filter(Course.lesson_name == data.course_name).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    user_skills = [cs.skill.skill_name for cs in course.skills]

    interaction = UserInteraction(
        user_id=data.user_id,
        course_name=data.course_name,
        skills=user_skills,
        interest_score=data.interest_score
    )

    db.add(interaction)
    db.commit()
    db.refresh(interaction)

    return {"status": "ok", "interaction_id": interaction.id}


# ---------------------------
# Κλάση CourseRecommender
# ---------------------------
class DegreeRecommender:
    def __init__(self, db: Session):
        self.db = db

    def recommend_based_on_history(self, user_id: int, top_n: int = 10):
        history = self.db.query(UserInteraction).filter(UserInteraction.user_id == user_id).all()
        if not history:
            return []

        user_skills = set()
        for h in history:
            user_skills.update(h.skills or [])

        all_degrees = self.db.query(DegreeProgram).all()
        viewed_degrees = set([h.course_name for h in history])

        recommendations = []

        for degree in all_degrees:
            if degree.name in viewed_degrees:
                continue

            degree_skills = []
            for m in degree.courses:
                degree_skills.extend([s.skill_name for s in m.skills])

            common_skills = user_skills & set(degree_skills)
            score = len(common_skills)

            if score > 0:
                recommendations.append({
                    "degree_name": degree.name,
                    "score": score,
                    "matching_skills": list(common_skills),
                    "reason": "Based on your past selections"
                })

        return sorted(recommendations, key=lambda x: x["score"], reverse=True)[:top_n]


# ---------------------------
# Endpoint για personalized history-based recommendations
# ---------------------------
# ---------------------------
# Endpoint για personalized history-based degree recommendations
# ---------------------------
@router.get("/recommend/degrees/history/{user_id}")
def recommend_personalized_degree_history(user_id: int, top_n: int = 10, db: Session = Depends(get_db)):
    recommender = DegreeRecommender(db)   # <-- εδώ χρησιμοποιούμε τη νέα κλάση
    results = recommender.recommend_based_on_history(user_id, top_n)
    
    # Επιβεβαίωση ότι κάθε αντικείμενο έχει score
    for r in results:
        if "score" not in r:
            r["score"] = 0.0
    
    return {"user_id": user_id, "recommendations": results}
