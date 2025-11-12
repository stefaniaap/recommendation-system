from collections import defaultdict
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from backend.models import University, Course
import json
import re
import logging

# Config logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CourseRecommender:
    """Recommender για προτάσεις μαθημάτων και πτυχίων ανά πανεπιστήμιο."""

    def __init__(self, db: Session):
        self.db = db

    # ==========================================================
    # 🔹 Βοηθητικές μέθοδοι (Helper Methods)
    # ==========================================================
    def get_university(self, univ_id: int) -> Optional[University]:
        return self.db.query(University).filter_by(university_id=univ_id).first()

    def get_all_universities(self) -> List[University]:
        return self.db.query(University).all()
    
    @staticmethod
    def normalize_name(name: str) -> str:
        if not name:
            return ""
        cleaned_name = re.sub(r'[^a-zA-Z0-9\s\u0370-\u03FF\u1F00-\u1FFF]', '', name)
        return cleaned_name.strip().upper()

    @staticmethod
    def _parse_titles(raw_titles):
        if not raw_titles:
            return []
        titles = []
        try:
            if isinstance(raw_titles, str):
                try:
                    parsed = json.loads(raw_titles)
                    titles = parsed if isinstance(parsed, list) else [parsed]
                except Exception:
                    titles = [raw_titles]
            elif isinstance(raw_titles, list):
                titles = raw_titles
            else:
                titles = [str(raw_titles)]
        except Exception:
            titles = []
        return [
            re.sub(r"[^a-zA-Z0-9 \-&\u0370-\u03FF\u1F00-\u1FFF]", "", str(t)).strip()
            for t in titles if t
        ]

    def get_course_details_by_name(self, course_name: str, target_univ_id: int) -> Dict[str, str]:
        course = self.db.query(Course).filter(
            Course.lesson_name == course_name,
            Course.university_id == target_univ_id
        ).first()

        if not course:
            course = self.db.query(Course).filter(
                Course.lesson_name == course_name
            ).first()

        if course:
            return {
                "description": (getattr(course, "description", "") or "Δεν βρέθηκε περιγραφή.").strip(),
                "objectives": (getattr(course, "objectives", "") or "Δεν βρέθηκαν στόχοι.").strip(),
                "learning_outcomes": (getattr(course, "learning_outcomes", "") or "Δεν βρέθηκαν μαθησιακά αποτελέσματα.").strip(),
                "course_content": (getattr(course, "course_content", "") or "Δεν βρέθηκε περιεχόμενο μαθήματος.").strip(),
            }
        
        return {
            "description": "Δεν βρέθηκε περιγραφή.",
            "objectives": "Δεν βρέθηκαν στόχοι.",
            "learning_outcomes": "Δεν βρέθηκαν μαθησιακά αποτελέσματα.",
            "course_content": "Δεν βρέθηκε περιεχόμενο μαθήματος.",
        }

    # ==========================================================
    # 1️⃣ Δημιουργία προφίλ ανά πτυχίο
    # ==========================================================
    def build_degree_profiles(self, univ_id: int) -> List[Dict[str, Any]]:
        profiles: List[Dict[str, Any]] = []
        university = self.get_university(univ_id)
        if not university or not getattr(university, "programs", []):
            return []

        for program in university.programs:
            program_id = getattr(program, "program_id", None)
            degree_type = (getattr(program, "degree_type", "") or "").strip()
            titles = self._parse_titles(getattr(program, "degree_titles", []))
            program_courses = getattr(program, "courses", [])
            courses = sorted({
                (c.lesson_name or "").strip()
                for c in program_courses
                if getattr(c, "lesson_name", None)
            })

            skills = set()
            for course in program_courses:
                for cs in getattr(course, "skills", []):
                    if getattr(cs, "skill", None):
                        skill_name = (cs.skill.skill_name or "").strip() 
                        if skill_name:
                            skills.add(skill_name)
            skills = sorted(list(skills))

            for title in titles:
                if not title:
                    continue
                profiles.append({
                    "university_id": univ_id,
                    "program_id": program_id,
                    "degree_title": title,
                    "degree_type": degree_type,
                    "skills": skills,
                    "courses": courses,
                })
        return profiles

    # ==========================================================
    # 2️⃣ Εύρεση παρόμοιων πτυχίων
    # ==========================================================
    def find_similar_degrees(
        self,
        target_profile: Dict[str, Any],
        all_profiles: List[Dict[str, Any]],
        top_n: int = 5,
    ) -> List[Dict[str, Any]]:
        if not target_profile or not all_profiles:
            return []

        degree_type = (target_profile.get("degree_type") or "").strip()
        target_text = " ".join(
            (target_profile.get("skills") or []) +
            (target_profile.get("courses") or [])
        ).strip()

        raw_candidates = [
            p for p in all_profiles
            if (p.get("degree_type") or "").strip() == degree_type
            and p.get("university_id") != target_profile.get("university_id")
        ]

        cand_objs, cand_texts = [], []
        for p in raw_candidates:
            text = " ".join((p.get("skills") or []) + (p.get("courses") or [])).strip()
            if text:
                cand_objs.append(p)
                cand_texts.append(text)

        if not target_text or not cand_texts:
            return []

        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform([target_text] + cand_texts)
        sims = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
        ranked = sorted(zip(cand_objs, sims), key=lambda x: x[1], reverse=True)
        return [p for p, _ in ranked[:top_n]]

    # ==========================================================
    # 3️⃣ Πρόταση μαθημάτων για ένα συγκεκριμένο πτυχίο
    # ==========================================================
    def suggest_courses_for_degree(
        self,
        target_degree: Dict[str, Any],
        similar_degrees: List[Dict[str, Any]],
        top_n: int = 10,
    ) -> List[Dict[str, Any]]:
        if not target_degree or not similar_degrees:
            return [{"info": "Δεν υπάρχουν διαθέσιμα παρόμοια πτυχία για σύσταση."}]

        target_skills = set(target_degree.get("skills", []))
        target_courses = set(target_degree.get("courses", []))

        course_freq = defaultdict(int)
        course_skills = defaultdict(set)
        course_specific_skills_map = dict()

        # Συγκέντρωση μαθημάτων και skills
        for deg in similar_degrees:
            deg_skills = set(deg.get("skills", []))
            for cname in deg.get("courses", []):
                if not cname or cname in target_courses:
                    continue

                db_course = self.db.query(Course).filter(Course.lesson_name == cname).first()
                course_specific_skills = set()
                if db_course:
                    for cs in getattr(db_course, "skills", []):
                        if getattr(cs, "skill", None):
                            skill_name = (cs.skill.skill_name or "").strip()
                            if skill_name:
                                course_specific_skills.add(skill_name)

                if course_specific_skills or deg_skills:
                    total_skills = deg_skills.union(course_specific_skills)
                    course_freq[cname] += 1
                    course_skills[cname].update(total_skills)
                    course_specific_skills_map[cname] = course_specific_skills

        if not course_freq:
            logger.info("Δεν βρέθηκαν νέα μαθήματα για πρόταση.")
            return [{"info": "Δεν βρέθηκαν νέα μαθήματα για πρόταση."}]

        courses_list = list(course_freq.keys())
        course_docs = [" ".join(course_skills[c]) for c in courses_list]
        target_doc = " ".join(target_skills)
        docs = course_docs + [target_doc]

        if all(not doc.strip() for doc in docs):
            logger.info("Η σύσταση απέτυχε λόγω έλλειψης δεξιοτήτων για σύγκριση.")
            return [{"info": "Η σύσταση απέτυχε λόγω έλλειψης δεξιοτήτων για σύγκριση."}]

        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(docs)
        sims = cosine_similarity(vectors[-1], vectors[:-1]).flatten()

        max_freq = max(course_freq.values()) if course_freq else 1
        target_univ_id = target_degree["university_id"]

        results = []
        for i, cname in enumerate(courses_list):
            skills = course_skills[cname]
            freq_score = course_freq[cname] / max_freq
            new_skills = course_specific_skills_map.get(cname, set()) - target_skills
            compat_skills = skills & target_skills

            intersection_size = len(compat_skills)
            union_size = len(skills | target_skills)
            compat_score = intersection_size / union_size if union_size else 0.0
            novelty_score = 1.0 - sims[i]
            new_skill_score = len(new_skills) / (len(skills) + 1)
            compatibility_factor = 1.0 if compat_score >= 0.1 else 0.05

            total_score = round(
                compatibility_factor * (
                    0.40 * freq_score +
                    0.35 * compat_score +
                    0.15 * new_skill_score +
                    0.10 * novelty_score
                ), 3
            )

            course_details = self.get_course_details_by_name(cname, target_univ_id)

            # =======================
            # DEBUG LOGS
            # =======================
            logger.info(f"Course: {cname}")
            logger.info(f"Total Skills: {skills}")
            logger.info(f"Specific Skills: {course_specific_skills_map.get(cname, set())}")
            logger.info(f"Target Skills: {target_skills}")
            logger.info(f"New Skills: {new_skills}")
            logger.info(f"Compatible Skills: {compat_skills}")
            logger.info(f"Freq Score: {freq_score}, Compat Score: {compat_score}, Novelty: {novelty_score}, NewSkillScore: {new_skill_score}")
            logger.info(f"Total Score: {total_score}")
            # =======================

            results.append({
    "course_name": cname,
    "score": total_score,
    "new_skills": sorted(list(new_skills)),
    "compatible_skills": sorted(list(compat_skills)),
    "description": course_details["description"],
    "objectives": course_details["objectives"],
    "learning_outcomes": course_details["learning_outcomes"],
    "course_content": course_details["course_content"],
})


        return sorted(results, key=lambda x: x["score"], reverse=True)[:top_n]