# backend/core.py
# -----------------------------------------
# Core Recommendation System για πανεπιστήμια
# -----------------------------------------
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.models import University
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import json
import re




class UniversityRecommender:
    def __init__(self, db: Session):
        """Αρχικοποίηση με session της βάσης δεδομένων."""
        self.db = db


    # ------------------------------
    # Build profile
    # ------------------------------
    def build_university_profile(self, university_id: int) -> Dict[str, Any]:
        """
        Επιστρέφει ένα προφίλ του πανεπιστημίου:
         - skills: λίστα δεξιοτήτων ESCO (όνομα + ESCO ID)
         - courses: λίστα μαθημάτων (χωρίς διπλότυπα)
         - degrees: λίστα τίτλων πτυχίων (καθαρισμένα)
        """
        university = self.db.query(University).filter_by(university_id=university_id).first()
        if not university:
            return None


        profile = {
            "skills": set(),
            "courses": [],
            "degrees": set(),
        }


        # === Μαθήματα & Δεξιότητες ===
        for course in university.courses:
            if course.lesson_name:
                profile["courses"].append(course.lesson_name.strip())


            for cs in course.skills:
                if getattr(cs, "skill", None):
                    esco_id = cs.skill.esco_id or "N/A"
                    skill_name = (cs.skill.skill_name or "").strip()
                    if skill_name:
                        esco_label = f"{skill_name} (ESCO: {esco_id})"
                        profile["skills"].add(esco_label)


        # === Τίτλοι πτυχίων ===
        for program in university.programs:
            titles = program.degree_titles
            if not titles:
                continue
            if isinstance(titles, str):
                try:
                    titles = json.loads(titles)
                except Exception:
                    titles = [titles]
            try:
                for title in titles:
                    if not title:
                        continue
                    clean_title = re.sub(r"[^a-zA-Z0-9 \-&]", "", str(title)).strip()
                    if clean_title:
                        profile["degrees"].add(clean_title)
            except TypeError:
                clean_title = re.sub(r"[^a-zA-Z0-9 \-&]", "", str(titles)).strip()
                if clean_title:
                    profile["degrees"].add(clean_title)


        profile["skills"] = sorted(profile["skills"])
        profile["courses"] = sorted(list({c for c in profile["courses"] if c}))
        profile["degrees"] = sorted(profile["degrees"])


        return profile


    # ------------------------------
    # Similarity: combined (skills + courses + degrees)
    # ------------------------------
    def find_similar_universities(self, target_univ_id: int, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Βρίσκει παρόμοια πανεπιστήμια με βάση συνδυασμό:
         - skills (ESCO)
         - courses (ονόματα μαθημάτων)
         - degrees (τίτλοι πτυχίων)
        Χρησιμοποιεί TF-IDF + cosine similarity πάνω στο combined text.
        """
        target_profile = self.build_university_profile(target_univ_id)
        if not target_profile:
            return []


        all_univs = self.db.query(University).filter(University.university_id != target_univ_id).all()


        docs, valid_univs = [], []
        for u in all_univs:
            p = self.build_university_profile(u.university_id)
            if not p:
                continue
            parts = []
            if p["skills"]:
                parts.append(" ".join(p["skills"]))
            if p["courses"]:
                parts.append(" ".join(p["courses"]))
            if p["degrees"]:
                parts.append(" ".join(p["degrees"]))
            combined_text = " ".join(parts).strip()
            if combined_text:
                docs.append(combined_text)
                valid_univs.append(u)


        if not docs:
            return []


        tparts = []
        if target_profile["skills"]:
            tparts.append(" ".join(target_profile["skills"]))
        if target_profile["courses"]:
            tparts.append(" ".join(target_profile["courses"]))
        if target_profile["degrees"]:
            tparts.append(" ".join(target_profile["degrees"]))
        target_text = " ".join(tparts).strip()


        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(docs + [target_text])
        sims = cosine_similarity(vectors[-1], vectors[:-1]).flatten()


        ranked = sorted(zip(valid_univs, sims), key=lambda x: x[1], reverse=True)[:top_n]


        return [
            {
                "university_id": u.university_id,
                "name": u.university_name,
                "country": u.country,
                "similarity_score": round(float(score), 4),
            }
            for u, score in ranked
        ]




    # ------------------------------
    # Suggest degrees with skills
    # ------------------------------
    def suggest_degrees_with_skills(self, target_univ_id: int, top_n: int = 5):
        """
        Προτείνει νέα πτυχία λαμβάνοντας υπόψη:
         - Missing degrees (που υπάρχουν στα similar univs αλλά όχι στο target)
         - Missing skills (που υπάρχουν στα similar univs αλλά όχι στο target)
        """
        similar_univs = self.find_similar_universities(target_univ_id, top_n=10)
        target_profile = self.build_university_profile(target_univ_id)
        if not similar_univs or not target_profile:
            return []


        target_skills = set(target_profile["skills"])
        target_degrees = set(target_profile["degrees"])
        target_courses = set(target_profile["courses"])
        target_text = " ".join(target_profile["skills"] + target_profile["courses"] + target_profile["degrees"])


        degree_texts = {}
        degree_freq = defaultdict(int)
        degree_compat = defaultdict(float)
        degree_skill_bonus = defaultdict(float)


        for u in similar_univs:
            p = self.build_university_profile(u["university_id"])
            if not p:
                continue


            new_degrees = set(p["degrees"]) - target_degrees
            new_skills = set(p["skills"]) - target_skills
            combined_text = " ".join(p["skills"] + p["courses"])


            for deg in new_degrees:
                degree_freq[deg] += 1
                degree_texts[deg] = degree_texts.get(deg, "") + " " + combined_text
                overlap = len(set(p["skills"]) & target_skills)
                compat = overlap / (len(p["skills"]) + 1)
                degree_compat[deg] += compat
                degree_skill_bonus[deg] += len(new_skills)


        if not degree_texts:
            return [{"info": "No missing degrees detected among similar universities."}]


        degrees = list(degree_texts.keys())
        docs = [degree_texts[d] for d in degrees] + [target_text]
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(docs)
        sims = cosine_similarity(vectors[-1], vectors[:-1]).flatten()


        final = []
        max_freq = max(degree_freq.values()) if degree_freq else 1
        max_skill_bonus = max(degree_skill_bonus.values()) if degree_skill_bonus else 1


        for i, deg in enumerate(degrees):
            freq_score = degree_freq[deg] / max_freq
            novelty_score = 1 - sims[i]
            compat_score = degree_compat[deg] / degree_freq[deg]
            skill_enrichment_score = degree_skill_bonus[deg] / max_skill_bonus
         


            total_score = (
                0.30 * freq_score +
                0.25 * novelty_score +
                0.20 * compat_score +
                0.15 * skill_enrichment_score 
              
            )
            final.append((deg, round(total_score, 3)))


        final = sorted(final, key=lambda x: x[1], reverse=True)
        return [{"degree": d, "score": s} for d, s in final[:top_n]]


