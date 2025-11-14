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
    summary="Προτείνει μαθήματα για ένα ΝΕΟ Πτυχίο, ανεξαρτήτως Πανεπιστημίου."
)
async def recommend_courses_for_new_degree(
    degree_name: str = Path(..., description="Το κωδικοποιημένο όνομα του νέου Πτυχίου (URL-encoded)"),
    top_n_courses: int = 10,
    db: Session = Depends(get_db)
):
    """
    Επιστρέφει προτεινόμενα μαθήματα για ένα νέο πτυχίο, βασισμένο σε παρόμοια πτυχία άλλων πανεπιστημίων.
    Δεν αποκλείει μαθήματα που μπορεί να υπάρχουν ήδη, γιατί πρόκειται για εντελώς νέο πτυχίο.
    """
    try:
        decoded_degree_name = unquote(degree_name).strip()
        recommender = CourseRecommenderV2(db)

        logger.info(f"Request for new degree_name='{decoded_degree_name}'")

        # 1️⃣ Συλλογή όλων των προφίλ
        all_univs = recommender.get_all_universities()
        all_profiles: List[Dict[str, Any]] = []
        for u in all_univs:
            profiles = recommender.build_degree_profiles(u.university_id)
            if profiles:
                all_profiles.extend(profiles)

        if not all_profiles:
            logger.warning("No degree profiles found in any university.")
            raise HTTPException(status_code=404, detail="Δεν βρέθηκαν προφίλ πτυχίων σε κανένα πανεπιστήμιο.")

        # 2️⃣ Εύρεση παρόμοιων πτυχίων που ταιριάζουν στο όνομα (ή γενικά σε όλα)
        similar_degrees = [
            p for p in all_profiles
            if recommender.normalize_name(p.get("degree_title")) == recommender.normalize_name(decoded_degree_name)
        ]

        if not similar_degrees:
            logger.info("No exact degree name matches, using all profiles as similar degrees.")
            similar_degrees = all_profiles  # fallback: όλα τα προφίλ

        # 3️⃣ Συγκέντρωση skills για το νέο πτυχίο
        all_skills = set()
        for p in similar_degrees:
            all_skills.update(p.get("skills", []) or [])

        # 4️⃣ Πρόταση μαθημάτων για νέο πτυχίο
        try:
            result = recommender.suggest_courses_for_new_degree(
                similar_degrees=similar_degrees,
                target_skills=all_skills,
                top_n=top_n_courses
            )
        except Exception as e:
            logger.error(f"Error in suggest_courses_for_new_degree: {e}")
            raise HTTPException(status_code=500, detail="Η σύσταση απέτυχε λόγω εσωτερικού σφάλματος.")

        # 5️⃣ Δημιουργία τελικής λίστας απαντήσεων
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

        # 6️⃣ Επιστροφή αποτελέσματος
        return CourseRecommendationsResponse(
            university_id=-1,  # Δεν υπάρχει συγκεκριμένο πανεπιστήμιο
            program_id=-1,
            degree=decoded_degree_name,
            recommendations=final_recommendations
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Unexpected error in recommend_courses_for_new_degree: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.get(
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
    """
    Επιστρέφει προτεινόμενα μαθήματα για ένα συγκεκριμένο Πτυχίο, με βάση παρόμοια προγράμματα σπουδών.
    """
    try:
        decoded_degree_name = unquote(degree_name).strip()
        recommender = CourseRecommenderV2(db)


        logger.info(f"Request for university_id={university_id}, degree_name='{decoded_degree_name}'")

        # 1️⃣ Συλλογή όλων των προφίλ
        all_univs = recommender.get_all_universities()
        all_profiles: List[Dict[str, Any]] = []
        for u in all_univs:
            profiles = recommender.build_degree_profiles(u.university_id)
            if profiles:
                all_profiles.extend(profiles)

        if not all_profiles:
            logger.warning("No degree profiles found in any university.")
            raise HTTPException(status_code=404, detail="Δεν βρέθηκαν προφίλ πτυχίων σε κανένα πανεπιστήμιο.")

        # 2️⃣ Εύρεση αντιπροσωπευτικών προφίλ για το πτυχίο
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

        # 3️⃣ Δημιουργία συνθετικού "target degree"
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

        # 4️⃣ Εύρεση παρόμοιων πτυχίων
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

        # 5️⃣ Πρόταση μαθημάτων
        try:
            result = recommender.suggest_courses_for_degree(
                synthetic_target_degree,
                similar_degrees,
                top_n=top_n_courses
            )
        except Exception as e:
            logger.error(f"Error in suggest_courses_for_degree: {e}")
            raise HTTPException(status_code=500, detail="Η σύσταση απέτυχε λόγω εσωτερικού σφάλματος.")

        # 6️⃣ Δημιουργία τελικής λίστας απαντήσεων
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

        # 7️⃣ Επιστροφή αποτελέσματος
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


        
@router.get("/recommend/degrees/{university_id}")
def recommend_degrees(university_id: int, top_n: int = 5, db: Session = Depends(get_db)):
    recommender = UniversityRecommender(db)
    results = recommender.suggest_degrees_with_skills(university_id, top_n=top_n)
    return {"university_id": university_id, "recommended_degrees": results}






@router.get("/recommendations/university/{univ_id}")
def suggest_courses_for_university(univ_id: int, top_n: int = 10, db: Session = Depends(get_db)):
    recommender = CourseRecommenderV2(db)
    result = recommender.suggest_courses(univ_id, top_n)
    return {"university_id": univ_id, "recommendations": result}


@router.post("/recommend/personalized")
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
