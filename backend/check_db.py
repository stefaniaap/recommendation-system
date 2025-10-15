from backend.database import DB, SessionLocal
from backend.models import University

print("=== Έλεγχος σύνδεσης με βάση ===")

try:
    db = DB(SessionLocal())
    print("✅ Σύνδεση επιτυχής")
except Exception as e:
    print("❌ Σφάλμα σύνδεσης:", e)
    exit()

# Πανεπιστήμια
universities = db.get_all_universities()
print("Βρέθηκαν πανεπιστήμια:", len(universities))
for u in universities:
    print(f"- {u.university_id}: {u.university_name}")

# Λεπτομέρειες για πρώτο πανεπιστήμιο
if universities:
    univ_id = universities[0].university_id
    print(f"\nΛεπτομέρειες για Πανεπιστήμιο ID={univ_id}")
    print("Degrees:", db.get_degrees(univ_id))
    print("Courses:", db.get_courses_with_degree(univ_id))
    print("Skills:", db.get_skills(univ_id))
