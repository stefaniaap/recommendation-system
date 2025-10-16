# backend/evaluation.py
import re
from backend.database import SessionLocal
from backend.core2 import CourseRecommender
from backend.models import University
from sklearn.metrics import precision_score, recall_score, f1_score

TOP_N = 10  # πόσα προτεινόμενα courses ανά degree

def evaluate_recommender(db):
    recommender = CourseRecommender(db)
    results = []

    # Παίρνουμε όλα τα πανεπιστήμια
    universities = db.query(University).all()
    if not universities:
        print("⚠️ Δεν βρέθηκαν πανεπιστήμια στη βάση.")
        return []

    for univ in universities:
        print(f"\n🧩 Αξιολόγηση Πανεπιστημίου: {univ.university_name} (ID: {univ.university_id})")

        # === Δημιουργία ground truth από υπάρχοντα δεδομένα ===
        ground_truth = {}
        programs = getattr(univ, "programs", [])
        for prog in programs:
            courses = getattr(prog, "courses", [])
            course_names = sorted({(c.lesson_name or "").strip() for c in courses if c.lesson_name})
            if not course_names:
                continue

            titles = prog.degree_titles
            if isinstance(titles, str):
                import json
                try:
                    titles = json.loads(titles)
                    if not isinstance(titles, list):
                        titles = [titles]
                except Exception:
                    titles = [titles]
            elif not isinstance(titles, list):
                titles = [str(titles)]

            for title in titles:
                if not title:
                    title = f"Program_{prog.program_id}"
                clean_title = re.sub(r"[^a-zA-Z0-9 \-&]", "", title).strip()
                if clean_title:
                    ground_truth[clean_title] = course_names

        if not ground_truth:
            print(f"⚠️ Το πανεπιστήμιο {univ.university_name} δεν έχει διαθέσιμα μαθήματα στη βάση.")
            continue

        # === Λαμβάνουμε τις προτάσεις από το recommender ===
        suggestions = recommender.suggest_courses(univ.university_id, top_n=TOP_N)
        existing_degrees = suggestions.get("existing_degrees", {})

        for degree_title, true_courses in ground_truth.items():
            pred_courses = existing_degrees.get(degree_title, [])
            if isinstance(pred_courses, dict) and "info" in pred_courses:
                pred_courses = []

            pred_course_names = [c["course"] for c in pred_courses]

            print(f"\n🎓 Degree: {degree_title}")
            print(f"   True Courses: {true_courses}")
            print(f"   Predicted Courses: {pred_course_names}")

            if not pred_course_names or not true_courses:
                continue

            # === Case-insensitive σύγκριση ===
            all_courses = list(set([c.lower() for c in pred_course_names] + [c.lower() for c in true_courses]))
            y_true = [1 if c in [t.lower() for t in true_courses] else 0 for c in all_courses]
            y_pred = [1 if c in [p.lower() for p in pred_course_names] else 0 for c in all_courses]

            precision = precision_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)

            results.append({
                "university_id": univ.university_id,
                "university_name": univ.university_name,
                "degree_title": degree_title,
                "precision": round(precision, 3),
                "recall": round(recall, 3),
                "f1_score": round(f1, 3),
            })

    return results

if __name__ == "__main__":
    db = SessionLocal()
    try:
        eval_results = evaluate_recommender(db)
        print("\n📊 Αποτελέσματα αξιολόγησης:")
        for r in eval_results:
            print(r)
    finally:
        db.close()
