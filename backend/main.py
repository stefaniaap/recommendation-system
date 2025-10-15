# ===========================================
# backend/main.py
# FastAPI backend για Academic Recommender
# Σύστημα Συστάσεων Ακαδημαϊκών Προγραμμάτων
# ===========================================

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

# Υποθέτουμε ότι αυτά τα modules είναι σωστά ρυθμισμένα
from backend.database import get_db, init_db
from backend.core import UniversityRecommender
from backend.core2 import CourseRecommender

app = FastAPI(title="Academic Recommender API", version="1.0")

# ======================================================
# Startup event - Δημιουργεί τις βάσεις αν δεν υπάρχουν
# ======================================================
@app.on_event("startup")
def startup_event():
    """Διαδικασία εκκίνησης: Δημιουργία βάσης δεδομένων."""
    try:
        init_db()
    except Exception as e:
        # Αυτό το μήνυμα θα εμφανιστεί στην κονσόλα του server
        print(f"Error initializing DB: {e}")

# ======================================================
# Βασικά Endpoints (Πληροφορίες & Έλεγχος)
# ======================================================
@app.get("/")
def read_root():
    """Έλεγχος λειτουργίας Backend."""
    return {"message": "Backend is running successfully 🚀"}

@app.get("/test")
def test():
    """API Test endpoint."""
    return {"status": "ok", "info": "API test successful!"}

# ======================================================
# Προβολή προφίλ πανεπιστημίου
# ======================================================
@app.get("/profile/{univ_id}", response_model=Dict[str, Any])
def get_profile(univ_id: int, db: Session = Depends(get_db)):
    """Επιστρέφει το ακαδημαϊκό αποτύπωμα ενός πανεπιστημίου (Skills, Courses, Degrees)."""
    try:
        recommender = UniversityRecommender(db)
        profile = recommender.build_university_profile(univ_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Δεν βρέθηκε πανεπιστήμιο με ID={univ_id}")
        return profile
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Σφάλμα κατά τη δημιουργία προφίλ: {str(e)}")

# ======================================================
# Εύρεση παρόμοιων πανεπιστημίων (University Recommender)
# ======================================================
@app.get("/similar/{univ_id}")
def get_similar(univ_id: int, top_n: int = 5, db: Session = Depends(get_db)):
    """Επιστρέφει τα Top N πιο παρόμοια πανεπιστήμια με βάση το συνδυαστικό προφίλ (TF-IDF)."""
    try:
        recommender = UniversityRecommender(db)
        # Εδώ ελέγχεται αν υπάρχει το target university, το find_similar_universities το κάνει
        similar_univs = recommender.find_similar_universities(univ_id, top_n=top_n)
        return {"target_university_id": univ_id, "similar_universities": similar_univs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Σφάλμα κατά την εύρεση παρόμοιων: {str(e)}")

# ======================================================
# 1. Προτάσεις νέων πτυχίων (Degrees) - GAP ANALYSIS
# ======================================================
@app.get("/recommend/degrees/{university_id}")
def recommend_degrees(university_id: int, top_n: int = 5, db: Session = Depends(get_db)):
    """Προτείνει νέους τίτλους πτυχίων (Degrees) βασισμένους σε κενά προσφοράς και Skills."""
    try:
        recommender = UniversityRecommender(db)
        results = recommender.suggest_degrees_with_skills(university_id, top_n=top_n)
        return {"university_id": university_id, "recommended_degrees": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Σφάλμα κατά την πρόταση πτυχίων: {str(e)}")


# ======================================================
# 2. Προτάσεις μαθημάτων (Courses) για ΟΛΑ τα πτυχία του Πανεπιστημίου
# (Χρησιμοποιεί την ακριβή ανάλυση του CourseRecommender)
# ======================================================
@app.get("/recommendations/university/{univ_id}")
def suggest_courses_for_university(univ_id: int, top_n: int = 10, db: Session = Depends(get_db)):
    """
    Προτείνει μαθήματα για όλα τα υπάρχοντα πτυχία, καθώς και για πιθανά νέα πτυχία,
    με βάση την ανάλυση κενών δεξιοτήτων (Skills Gap Analysis).
    """
    try:
        recommender = CourseRecommender(db)
        result = recommender.suggest_courses(univ_id, top_n)
        return {"university_id": univ_id, "recommendations": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Σφάλμα στην πρόταση μαθημάτων ανά πανεπιστήμιο: {str(e)}")


# ======================================================
# 3. Προτάσεις μαθημάτων (Courses) για ΕΝΑ ΣΥΓΚΕΚΡΙΜΕΝΟ Πτυχίο
# ======================================================
@app.get("/recommendations/degree/")
def suggest_for_degree(
    univ_id: int, 
    degree_title: str = Query(..., description="Ο πλήρης τίτλος του πτυχίου (π.χ. 'MSc in Computer Science')"), 
    top_n: int = 10, 
    db: Session = Depends(get_db)
):
    """
    Προτείνει μαθήματα για ένα συγκεκριμένο υπάρχον πτυχίο, 
    συγκρίνοντας το με παρόμοια πτυχία παγκοσμίως.
    """
    try:
        recommender = CourseRecommender(db)
        
        # 1. Εύρεση του target πτυχίου
        profiles = recommender.build_degree_profiles(univ_id)
        target_deg = next((p for p in profiles if p["degree_title"].strip() == degree_title.strip()), None)
        
        if not target_deg:
            raise HTTPException(status_code=404, detail=f"Δεν βρέθηκε το πτυχίο '{degree_title}' στο Πανεπιστήμιο ID={univ_id}.")

        # 2. Συγκέντρωση όλων των πτυχίων για σύγκριση
        all_profiles = []
        for u in recommender.get_all_universities():
            all_profiles += recommender.build_degree_profiles(u.university_id)

        # 3. Εύρεση παρόμοιων και πρόταση μαθημάτων
        similar = recommender.find_similar_degrees(target_deg, all_profiles)
        suggestions = recommender.suggest_courses_for_degree(target_deg, similar, top_n)
        
        if not similar:
             return {"university_id": univ_id, "degree_title": degree_title, "suggestions": [{"info": "Δεν βρέθηκαν αρκετά παρόμοια πτυχία για σύγκριση."}]}

        return {"university_id": univ_id, "degree_title": degree_title, "suggestions": suggestions}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Σφάλμα στην πρόταση μαθημάτων για πτυχίο: {str(e)}")