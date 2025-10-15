# test_recommender.py
from backend.core import RecommendationSystem

def main():
    # Βάλε εδώ το ID του πανεπιστημίου που θέλεις να δοκιμάσεις
    target_univ_id = 1
    top_k = 5

    recommender = RecommendationSystem()
    print("✅ RecommendationSystem initialized successfully.")

    # Παίρνουμε τις συστάσεις
    recommendations = recommender.recommend(target_univ_id, top_k=top_k)

    print("\n--- Recommendations ---")
    print("Degrees:")
    for d in recommendations["degrees"]:
        print(f"  {d['degree']} (score: {d['score']})")

    print("\nSkills:")
    for s in recommendations["skills"]:
        print(f"  {s['skill']} (score: {s['score']})")

    print("\nCourses:")
    for deg, courses in recommendations["courses"].items():
        print(f"  Degree: {deg}")
        for c in courses:
            print(f"    {c['course']} (score: {c['score']})")

if __name__ == "__main__":
    main()
