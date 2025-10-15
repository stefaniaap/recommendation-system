# test_recommender.py
from backend.core import RecommendationSystem
from backend.database import SessionLocal, DB
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def test_recommendations(univ_ids, top_k=5):
    rs = RecommendationSystem()
    
    with SessionLocal() as session:
        db = DB(session)
        all_univs = db.get_all_universities()
        print(f"Found {len(all_univs)} universities in DB.\n")

    for univ_id in univ_ids:
        print(f"--- Recommendations for University ID {univ_id} ---")
        try:
            profile = rs.get_university_profile(univ_id)
            print(f"Degrees: {profile['degrees']}")
            print(f"Courses: {profile['courses']}")
            print(f"Skills: {profile['skills']}")
            
            recs = rs.recommend(univ_id, top_k=top_k)
            
            print("\nMissing Degrees:")
            for d in recs['degrees']:
                print(f"  {d['degree']} | score={d['score']}")
            
            print("\nMissing Skills:")
            for s in recs['skills']:
                print(f"  {s['skill']} | score={s['score']}")
            
            print("\nMissing Courses:")
            for deg, courses in recs['courses'].items():
                print(f"  Degree: {deg}")
                for c in courses:
                    print(f"    {c['course']} | score={c['score']}")
            
            print("\n" + "="*50 + "\n")
        except Exception as e:
            logger.error(f"Error testing university {univ_id}: {e}")

if __name__ == "__main__":
    # Βάλε εδώ 2-3 university_ids που υπάρχουν στη βάση σου
    test_univ_ids = [1, 2, 3]
    test_recommendations(test_univ_ids)
