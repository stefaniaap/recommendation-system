# backend/core3.py
# ------------------------------------------------------------
# CourseRecommender για Personalized Recommendations
# Χρησιμοποιεί TF-IDF και Cosine Similarity για skills matching
# ------------------------------------------------------------

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.models import DegreeProgram, University, Course, Skill, CourseSkill

class CourseRecommender:
    def __init__(self, db: Session):
        self.db = db

    def recommend_personalized(
        self,
        target_skills: List[str],
        language: Optional[str] = None,
        country: Optional[str] = None,
        degree_type: Optional[str] = None,
        top_n: int = 10,
    ) -> Dict[str, Any]:
        """
        Return personalized recommendations for degrees and free courses.
        """

        # --- Normalize user skills ---
        target_skills_norm = [s.lower().strip() for s in target_skills if s]
        user_text = " ".join(target_skills_norm)

        if not user_text:
            return {"message": "Παρακαλώ εισάγετε τουλάχιστον μία δεξιότητα."}

        # --- Gather all degrees with filters ---
        query = self.db.query(DegreeProgram).join(University)
        if language:
            query = query.filter(DegreeProgram.language.ilike(f"%{language}%"))
        if country:
            query = query.filter(University.country.ilike(f"%{country}%"))
        if degree_type:
            query = query.filter(DegreeProgram.degree_type.ilike(f"%{degree_type}%"))

        programs = query.all()
        if not programs:
            return {"message": "Δεν βρέθηκαν σχετικά προγράμματα."}

        # --- Build program profiles (skills from courses) ---
        program_texts, program_objs = [], []
        for prog in programs:
            skills = self._get_program_skills(prog.program_id)
            if not skills:
                continue
            text = " ".join([s.lower() for s in skills])
            program_texts.append(text)
            program_objs.append(prog)

        if not program_texts:
            return {"message": "Δεν υπάρχουν skills σε κανένα πρόγραμμα."}

        # --- Vectorize and compute similarity ---
        vectorizer = TfidfVectorizer()
        try:
            all_docs = [user_text] + program_texts
            vectors = vectorizer.fit_transform(all_docs)
            sims = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
        except Exception as e:
            print(f"TF-IDF vectorization error: {e}")
            sims = [0.0] * len(program_objs)

        # --- Score adjustment based on filters ---
        scored_programs = []
        for i, prog in enumerate(program_objs):
            score = sims[i]
            if language and prog.language and prog.language.lower() == language.lower():
                score += 0.05
            if degree_type and prog.degree_type and prog.degree_type.lower() == degree_type.lower():
                score += 0.05
            if country and prog.university.country and prog.university.country.lower() == country.lower():
                score += 0.05
            scored_programs.append({
                "program_id": prog.program_id,
                "degree_name": getattr(prog, 'degree_name', "N/A"),
                "university": prog.university.university_name,
                "language": prog.language,
                "country": prog.university.country,
                "degree_type": prog.degree_type,
                "score": round(score, 3)
            })

        scored_programs = sorted(scored_programs, key=lambda x: x["score"], reverse=True)[:top_n]

        # --- Find unlinked courses (not part of a degree) ---
        unlinked_courses = self.db.query(Course).filter(Course.program_id == None).all()
        course_texts, course_objs = [], []
        for c in unlinked_courses:
            skills = self._get_course_skills(c.course_id)
            if skills:
                course_texts.append(" ".join([s.lower() for s in skills]))
                course_objs.append(c)

        unlinked_recs = []
        if course_texts:
            try:
                all_docs = [user_text] + course_texts
                vectors = vectorizer.fit_transform(all_docs)
                sims = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
                for i, c in enumerate(course_objs):
                    unlinked_recs.append({
                        "course_id": c.course_id,
                        "lesson_name": c.lesson_name,
                        "university": c.university.university_name,
                        "score": round(sims[i], 3)
                    })
                unlinked_recs = sorted(unlinked_recs, key=lambda x: x["score"], reverse=True)[:top_n]
            except Exception as e:
                print(f"TF-IDF error for unlinked courses: {e}")
                unlinked_recs = []

        # --- Group skills alphabetically by category ---
        grouped_skills = self._group_skills_by_category(target_skills_norm)

        return {
            "recommended_programs": scored_programs,
            "recommended_unlinked_courses": unlinked_recs,
            "skills_by_category": grouped_skills
        }

    # ========================
    # Helper Methods
    # ========================
    def _get_program_skills(self, program_id: int) -> List[str]:
        """
        Επιστρέφει όλα τα skills ενός DegreeProgram
        αντλώντας τα από όλα τα courses του προγράμματος.
        """
        program = self.db.query(DegreeProgram).filter_by(program_id=program_id).first()
        if not program:
            return []

        skills_set = set()
        for course in program.courses:
            for cs in getattr(course, "skills", []):
                try:
                    skills_set.add(cs.skill.skill_name)
                except Exception:
                    continue
        return list(skills_set)

    def _get_course_skills(self, course_id: int) -> List[str]:
        """
        Επιστρέφει τα skills ενός συγκεκριμένου μαθήματος.
        """
        skills = []
        try:
            for cs in self.db.query(CourseSkill).filter_by(course_id=course_id).all():
                if hasattr(cs, "skill") and hasattr(cs.skill, "skill_name"):
                    skills.append(cs.skill.skill_name)
        except Exception:
            pass
        return skills

    def _group_skills_by_category(self, skills: List[str]) -> Dict[str, List[str]]:
        """
        Ομαδοποιεί τις δεξιότητες ανά κατηγορία (αν υπάρχει),
        αλλιώς μπαίνει στην κατηγορία 'Άλλες'.
        """
        grouped = {}
        for s in skills:
            try:
                skill_obj = self.db.query(Skill).filter(Skill.skill_name.ilike(f"%{s}%")).first()
                cat = "Άλλες"
                if skill_obj:
                    if isinstance(skill_obj.categories, dict):
                        cat = skill_obj.categories.get("preferredLabel", "Άλλες")
                    elif skill_obj.categories:
                        cat = str(skill_obj.categories)
                grouped.setdefault(cat, []).append(s)
            except Exception as e:
                print(f"Warning: couldn't group skill '{s}': {e}")
                grouped.setdefault("Άλλες", []).append(s)

        # Ταξινόμηση skills μέσα σε κάθε κατηγορία
        for k in grouped:
            grouped[k] = sorted(set(grouped[k]), key=lambda x: x.lower())
        return dict(sorted(grouped.items()))
