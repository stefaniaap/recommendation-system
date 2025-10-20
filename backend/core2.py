# =============================================
# backend/core2.py (ΤΕΛΙΚΑ ΔΙΟΡΘΩΜΕΝΟ)
# =============================================

from collections import defaultdict
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from backend.models import University
import json
import re

class CourseRecommender:
    """Recommender για προτάσεις μαθημάτων και πτυχίων ανά πανεπιστήμιο."""

    def __init__(self, db: Session):
        self.db = db

    # ==========================================================
    # 🔹 Βοηθητικές μέθοδοι (ΕΠΙΒΕΒΑΙΩΜΕΝΕΣ)
    # ==========================================================
    def get_university(self, univ_id: int):
        """Επιστρέφει αντικείμενο University από τη βάση."""
        return self.db.query(University).filter_by(university_id=univ_id).first()

    def get_all_universities(self):
        """Επιστρέφει όλα τα πανεπιστήμια από τη βάση."""
        return self.db.query(University).all()
    
    @staticmethod
    def normalize_name(name: str) -> str:
        """Αφαιρεί κενά, σημεία στίξης, και μετατρέπει σε κεφαλαία για ασφαλή σύγκριση."""
        if not name:
            return ""
        cleaned_name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
        return cleaned_name.strip().upper()

    @staticmethod
    def _parse_titles(raw_titles):
        """Μετατρέπει string ή JSON titles σε λίστα καθαρών τίτλων."""
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
            re.sub(r"[^a-zA-Z0-9 \-&]", "", str(t)).strip()
            for t in titles if t
        ]

    # ==========================================================
    # 1️⃣ Δημιουργία προφίλ ανά πτυχίο (ΔΙΟΡΘΩΜΕΝΟ)
    # ==========================================================
    def build_degree_profiles(self, univ_id: int) -> List[Dict[str, Any]]:
        """
        Δημιουργεί λίστα από degree profiles για το πανεπιστήμιο.
        """
        profiles: List[Dict[str, Any]] = []
        university = self.get_university(univ_id)
        if not university or not getattr(university, "programs", []):
            return []

        for program in university.programs:
            program_id = getattr(program, "program_id", None)
            degree_type = (getattr(program, "degree_type", "") or "").strip()
            titles = self._parse_titles(getattr(program, "degree_titles", []))

            # Συλλογή μαθημάτων (Courses) - Λόγω relationship στο models.py, 
            # παίρνουμε τα μαθήματα που συνδέονται με το program_id.
            program_courses = getattr(program, "courses", [])
            courses = sorted({
                (c.lesson_name or "").strip()
                for c in program_courses
                if getattr(c, "lesson_name", None)
            })

            # Συλλογή δεξιοτήτων (Skills) - Από τα μαθήματα του συγκεκριμένου προγράμματος
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
    # 2️⃣ Εύρεση παρόμοιων πτυχίων (Παραμένει ως είχε)
    # ==========================================================
    def find_similar_degrees(
        self,
        target_profile: Dict[str, Any],
        all_profiles: List[Dict[str, Any]],
        top_n: int = 5,
    ) -> List[Dict[str, Any]]:
        """Επιστρέφει παρόμοια πτυχία με βάση skills + degree_type."""
        if not target_profile or not all_profiles:
            return []

        degree_type = target_profile.get("degree_type", "")

        candidates = [
            p for p in all_profiles
            if p.get("degree_type", "") == degree_type
            and p.get("university_id") != target_profile.get("university_id")
            and p.get("skills")
        ]
        if not candidates:
            return []

        # Συνδυασμός skills + courses για πιο θεματική σύγκριση
        target_text = " ".join(target_profile.get("skills", []) + target_profile.get("courses", []))
        docs = [
             " ".join(p.get("skills", []) + p.get("courses", []))
             for p in candidates
        ]
        docs_with_target = [target_text] + docs


        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(docs_with_target)
        
        sims = cosine_similarity(vectors[0:1], vectors[1:]).flatten()

        ranked = sorted(zip(candidates, sims), key=lambda x: x[1], reverse=True)
        return [p for p, _ in ranked[:top_n]]

    # ==========================================================
    # 3️⃣ Πρόταση μαθημάτων για ένα συγκεκριμένο πτυχίο (Παραμένει ως είχε)
    # ==========================================================
    def suggest_courses_for_degree(
        self,
        target_degree: Dict[str, Any],
        similar_degrees: List[Dict[str, Any]],
        top_n: int = 10,
    ) -> List[Dict[str, Any]]:
        """Προτείνει μαθήματα για συγκεκριμένο πτυχίο, δίνοντας έμφαση στη συνάφεια (compatibility)."""
        if not target_degree or not similar_degrees:
            # Επιστρέφουμε list με dict info, το οποίο φιλτράρεται στο main.py
            return [{"info": "Δεν υπάρχουν διαθέσιμα παρόμοια πτυχία."}]

        target_skills = set(target_degree.get("skills", []))
        target_courses = set(target_degree.get("courses", []))

        course_freq = defaultdict(int)
        course_skills = defaultdict(set)

        # Συγκέντρωση μαθημάτων και skills από παρόμοια πτυχία
        for deg in similar_degrees:
            deg_skills = set(deg.get("skills", []))
            for course in deg.get("courses", []):
                if not course or course in target_courses:
                    continue
                
                course_freq[course] += 1
                course_skills[course].update(deg_skills)

        if not course_freq:
            return [{"info": "Δεν βρέθηκαν νέα μαθήματα."}]

        # Δημιουργία texts για TF-IDF/Cosine Similarity
        course_docs = [" ".join(course_skills[c]) for c in course_freq]
        target_doc = " ".join(target_skills)
        docs = course_docs + [target_doc]
        
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(docs)
        
        sims = cosine_similarity(vectors[-1], vectors[:-1]).flatten()

        results = []
        max_freq = max(course_freq.values()) if course_freq else 1

        for i, cname in enumerate(course_freq.keys()):
            skills = course_skills[cname]
            
            # Υπολογισμός Συντελεστών
            freq_score = course_freq[cname] / max_freq
            new_skills = skills - target_skills
            
            # Υπολογισμός Compatibility Score (Jaccard Index)
            intersection_size = len(skills & target_skills)
            union_size = len(skills | target_skills)
            compat_score = intersection_size / union_size if union_size else 0.0

            novelty_score = 1.0 - sims[i]
            new_skill_score = len(new_skills) / (len(skills) + 1)
            
            # Εισαγωγή Compatibility Factor
            compatibility_factor = 1.0 if compat_score >= 0.1 else 0.05
            
            # Τελική Συνάρτηση Βαθμολόγησης
            total_score = round(
                compatibility_factor * (
                    0.40 * freq_score +
                    0.35 * compat_score +
                    0.15 * new_skill_score +
                    0.10 * novelty_score
                ),
                3
            )

            results.append({
                "course": cname,
                "score": total_score,
                "new_skills": sorted(new_skills),
                "compatible_skills": sorted(skills & target_skills),
            })

        return sorted(results, key=lambda x: x["score"], reverse=True)[:top_n]
    
    # ==========================================================
    # 4️⃣.1 Προτάσεις μαθημάτων για ΥΠΑΡΧΟΝΤΑ πτυχία (Παραμένει ως είχε)
    # ==========================================================
    def suggest_courses_for_existing_degrees(
        self,
        target_univ_id: int,
        all_profiles: List[Dict[str, Any]],
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Προτείνει μαθήματα για κάθε υπάρχον πτυχίο του πανεπιστημίου.
        """
        target_profiles = self.build_degree_profiles(target_univ_id)
        if not target_profiles:
            return {"info": "Δεν βρέθηκαν υπάρχοντα πτυχία για ανάλυση."}

        suggestions = {}
        
        for target_deg in target_profiles:
            similar = self.find_similar_degrees(target_deg, all_profiles, top_n=5)
            if not similar:
                continue
                
            suggested = self.suggest_courses_for_degree(target_deg, similar, top_n)
            title = target_deg["degree_title"].strip()
            suggestions[title] = suggested

        return suggestions or {"info": "Δεν βρέθηκαν υπάρχοντα πτυχία για ανάλυση."}

    # ==========================================================
    # 4️⃣.2 Προτάσεις για ΠΙΘΑΝΑ ΝΕΑ πτυχία (Παραμένει ως είχε)
    # ==========================================================
    def suggest_new_degree_proposals(
        self,
        target_univ_id: int,
        all_profiles: List[Dict[str, Any]],
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Προτείνει πιθανά νέα πτυχία για το πανεπιστήμιο.
        """
        target_profiles = self.build_degree_profiles(target_univ_id)
        target_titles = {d["degree_title"] for d in target_profiles}
        
        candidate_titles = {d["degree_title"] for d in all_profiles} - target_titles

        new_degree_suggestions = []
        for cand_title in candidate_titles:
            cand_degrees = [d for d in all_profiles if d["degree_title"] == cand_title]
            if not cand_degrees:
                continue

            agg_courses = defaultdict(int)
            for d in cand_degrees:
                for c in d.get("courses", []):
                    agg_courses[c] += 1

            top_courses = sorted(agg_courses.items(), key=lambda x: x[1], reverse=True)[:top_n]
            
            new_degree_suggestions.append({
                "degree_title": cand_title,
                "suggested_courses": [{"course": c, "freq": f} for c, f in top_courses],
            })

        return new_degree_suggestions or [{"info": "Δεν εντοπίστηκαν νέα πιθανά πτυχία."}]

    # ==========================================================
    # 4️⃣.3 Ολοκληρωμένη πρόταση για όλο το πανεπιστήμιο (Παραμένει ως είχε)
    # ==========================================================
    def suggest_courses(self, target_univ_id: int, top_n: int = 10) -> Dict[str, Any]:
        """
        Προτείνει μαθήματα για υπάρχοντα και πιθανά νέα πτυχία.
        """
        all_univs = self.get_all_universities()
        all_profiles = []
        for u in all_univs:
            profiles = self.build_degree_profiles(u.university_id)
            if profiles:
                all_profiles.extend(profiles)
                
        if not all_profiles:
            return {"info": "Δεν βρέθηκαν διαθέσιμα προφίλ πτυχίων σε κανένα πανεπιστήμιο."}

        existing_suggestions = self.suggest_courses_for_existing_degrees(
            target_univ_id,
            all_profiles,
            top_n
        )
        
        new_degree_proposals = self.suggest_new_degree_proposals(
            target_univ_id,
            all_profiles,
            top_n
        )

        return {
            "existing_degrees": existing_suggestions,
            "new_degree_proposals": new_degree_proposals,
        }