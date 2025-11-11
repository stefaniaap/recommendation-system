# =============================================================
# backend/core3.py
# -------------------------------------------------------------
# Περιέχει δύο Recommendation Engines:
# 1. CourseRecommender        → Προτείνει προγράμματα και μαθήματα
# 2. CourseRecommenderV4      → Προτείνει electives για συγκεκριμένο πρόγραμμα
# -------------------------------------------------------------
# Χρησιμοποιεί TF-IDF & Cosine Similarity για σύγκριση δεξιοτήτων.
# =============================================================

from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
import re

from backend.models import DegreeProgram, University, Course, Skill, CourseSkill


# =============================================================
# 1️⃣ CourseRecommender — Personalized Degree & Course Matching
# =============================================================
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
        """Return personalized recommendations for degrees and free courses."""

        # --- Normalize user skills ---
        target_skills_norm = [s.lower().strip() for s in target_skills if s]
        user_text = " ".join(target_skills_norm)

        if not user_text:
            return {"message": "Παρακαλώ εισάγετε τουλάχιστον μία δεξιότητα."}

        # --- Gather degrees ---
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

        # --- Build program skill profiles ---
        program_texts, program_objs = [], []
        for prog in programs:
            skills = self._get_program_skills(prog.program_id)
            if not skills:
                continue
            program_texts.append(" ".join([s.lower() for s in skills]))
            program_objs.append(prog)

        if not program_texts:
            return {"message": "Δεν υπάρχουν skills σε κανένα πρόγραμμα."}

        # --- TF-IDF Similarity ---
        vectorizer = TfidfVectorizer()
        try:
            all_docs = [user_text] + program_texts
            vectors = vectorizer.fit_transform(all_docs)
            sims = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
        except Exception as e:
            print(f"TF-IDF vectorization error: {e}")
            sims = [0.0] * len(program_objs)

        # --- Score programs ---
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
                "degree_name": (
    (prog.degree_titles.get("el") if isinstance(prog.degree_titles, dict) and prog.degree_titles.get("el")
     else prog.degree_titles.get("en") if isinstance(prog.degree_titles, dict) and prog.degree_titles.get("en")
     else str(prog.degree_titles))
    if prog.degree_titles else "N/A"
),

                "university": prog.university.university_name,
                "language": prog.language,
                "country": prog.university.country,
                "degree_type": prog.degree_type,
                "score": round(score, 3)
            })

        scored_programs = sorted(scored_programs, key=lambda x: x["score"], reverse=True)[:top_n]

        # --- Unlinked courses ---
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
        skills = []
        try:
            for cs in self.db.query(CourseSkill).filter_by(course_id=course_id).all():
                if hasattr(cs, "skill") and hasattr(cs.skill, "skill_name"):
                    skills.append(cs.skill.skill_name)
        except Exception:
            pass
        return skills

    def _group_skills_by_category(self, skills: List[str]) -> Dict[str, List[str]]:
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
            except Exception:
                grouped.setdefault("Άλλες", []).append(s)
        for k in grouped:
            grouped[k] = sorted(set(grouped[k]), key=lambda x: x.lower())
        return dict(sorted(grouped.items()))


# =============================================================
# 2️⃣ CourseRecommenderV4 — Electives Recommendation per Program
# =============================================================
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def _normalize_skill(s: str) -> str:
    """Καθαρίζει και κανονικοποιεί ένα skill token."""
    if not s:
        return ""
    s = str(s).strip().lower()
    s = re.sub(r"[^a-z0-9\u0370-\u03FF\u1F00-\u1FFF\s\-\+\.#]", "", s)
    return s


class CourseRecommenderV4:
    """Προτείνει μαθήματα επιλογής (electives) για συγκεκριμένο πρόγραμμα & πανεπιστήμιο."""

    def __init__(self, db: Session, tfidf_weight: float = 0.6, overlap_weight: float = 0.4):
        self.db = db
        total = (tfidf_weight or 0.0) + (overlap_weight or 0.0)
        if total <= 0:
            self.tfidf_weight = 0.6
            self.overlap_weight = 0.4
        else:
            self.tfidf_weight = tfidf_weight / total
            self.overlap_weight = overlap_weight / total

    def recommend_electives_for_degree_enhanced(
        self,
        univ_id: int,
        program_id: int,
        target_skills: List[str],
        top_n: int = 10,
        min_overlap_ratio: float = 0.0,
    ) -> Dict[str, Any]:
        """Προτείνει electives για συγκεκριμένο πρόγραμμα σπουδών βάσει skills χρήστη."""
        user_skills_norm = [_normalize_skill(s) for s in (target_skills or []) if _normalize_skill(s)]
        user_skills_set: Set[str] = set(user_skills_norm)
        if not user_skills_set:
            return {"message": "Παρακαλώ εισάγετε τουλάχιστον μία (έγκυρη) δεξιότητα."}

        user_text = " ".join(sorted(user_skills_set))

        program = self.db.query(DegreeProgram).filter_by(program_id=program_id, university_id=univ_id).first()
        if not program:
            return {"message": "Δεν βρέθηκε το πρόγραμμα σπουδών για αυτό το πανεπιστήμιο."}

        # --- Filter electives ---
        elective_courses = []
        for c in getattr(program, "courses", []) or []:
            mand_opt = getattr(c, "mand_opt_list", None)
            is_optional = False
            if isinstance(mand_opt, str) and "optional" in mand_opt.lower():
                is_optional = True
            elif isinstance(mand_opt, (list, tuple, set)):
                for v in mand_opt:
                    if "optional" in str(v).lower():
                        is_optional = True
                        break
            if is_optional:
                elective_courses.append(c)

        if not elective_courses:
            return {"message": "Δεν υπάρχουν μαθήματα επιλογής για αυτό το πρόγραμμα."}

        course_objs, course_skill_texts, course_skill_sets, course_raw_skills = [], [], [], []

        for c in elective_courses:
            skill_names = []
            if hasattr(c, "courseskills"):
                for cs in getattr(c, "courseskills") or []:
                    if hasattr(cs, "skill") and getattr(cs.skill, "skill_name", None):
                        skill_names.append(str(cs.skill.skill_name))
            elif hasattr(c, "skills"):
                for cs in getattr(c, "skills") or []:
                    if hasattr(cs, "skill") and getattr(cs.skill, "skill_name", None):
                        skill_names.append(str(cs.skill.skill_name))
                    elif getattr(cs, "skill_name", None):
                        skill_names.append(str(cs.skill_name))
            if not skill_names:
                continue

            normalized = [_normalize_skill(s) for s in skill_names if _normalize_skill(s)]
            if not normalized:
                continue

            course_objs.append(c)
            course_skill_sets.append(set(normalized))
            course_skill_texts.append(" ".join(normalized))
            course_raw_skills.append(sorted(set(skill_names)))

        if not course_objs:
            return {"message": "Δεν βρέθηκαν skills στα μαθήματα επιλογής αυτού του προγράμματος."}

        # --- TF-IDF Similarity ---
        try:
            vectorizer = TfidfVectorizer()
            docs = [user_text] + course_skill_texts
            vectors = vectorizer.fit_transform(docs)
            tfidf_scores = cosine_similarity(vectors[0:1], vectors[1:]).flatten().tolist()
        except Exception as e:
            logger.exception("TF-IDF vectorization failed: %s", e)
            tfidf_scores = [0.0] * len(course_objs)

        # --- Compute scores ---
        scored = []
        for i, c in enumerate(course_objs):
            course_set = course_skill_sets[i]
            matched = sorted(list(user_skills_set & course_set))
            missing = sorted(list(course_set - user_skills_set))
            overlap_ratio = len(matched) / len(course_set | user_skills_set) if (course_set | user_skills_set) else 0.0
            tfidf_score = float(tfidf_scores[i]) if i < len(tfidf_scores) else 0.0
            if overlap_ratio < min_overlap_ratio and tfidf_score < 0.01:
                continue

            final_raw = (self.tfidf_weight * tfidf_score) + (self.overlap_weight * overlap_ratio)
            new_skill_count = len([s for s in course_set if s not in user_skills_set])
            new_skill_bonus = 0.02 * min(new_skill_count, 5)
            final_score = max(0.0, min(1.0, final_raw + new_skill_bonus))

            reason = []
            if matched:
                reason.append(f"Κοινές δεξιότητες: {len(matched)} ({', '.join(matched[:5])})")
            if new_skill_count:
                reason.append(f"Φέρνει νέες δεξιότητες: {new_skill_count}")
            if tfidf_score > 0.0:
                reason.append(f"Semantic similarity: {round(tfidf_score,3)}")
            reason_text = "; ".join(reason) if reason else "Χαμηλή συνάφεια."

            scored.append({
                "course_id": getattr(c, "course_id", None),
                "lesson_name": getattr(c, "lesson_name", None),
                "university": getattr(getattr(c, "university", None), "university_name", None),
                "final_score": round(final_score, 3),
                "tfidf_score": round(tfidf_score, 3),
                "overlap_ratio": round(overlap_ratio, 3),
                "matching_skills": matched,
                "missing_skills": missing,
                "reason": reason_text,
                "skills": course_raw_skills[i],
            })

        scored_sorted = sorted(scored, key=lambda x: x["final_score"], reverse=True)[:max(1, top_n)]

        return {
            "recommended_electives": scored_sorted,
            "meta": {
                "n_electives_considered": len(course_objs),
                "n_returned": len(scored_sorted),
                "tfidf_weight": self.tfidf_weight,
                "overlap_weight": self.overlap_weight,
            }
        }
