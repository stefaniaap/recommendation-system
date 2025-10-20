# =============================================
# backend/core.py (ΕΠΙΒΕΒΑΙΩΜΕΝΟ)
# =============================================

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.models import University # Σωστή εισαγωγή
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import json
import re

class UniversityRecommender:
    def __init__(self, db: Session):
        self.db = db
        self._profile_cache = {} 

    # ------------------------------
    # Build university profile
    # ------------------------------
    def build_university_profile(self, university_id: int) -> Dict[str, Any]:
        """Επιστρέφει ένα προφίλ του πανεπιστημίου."""
        if university_id in self._profile_cache:
            return self._profile_cache[university_id]
        
        university = self.db.query(University).filter_by(university_id=university_id).first()
        if not university:
            return None

        profile = {
            "skills": set(), 
            "skills_raw_names": set(), 
            "courses": [],
            "degrees": set(),
        }

        # === Μαθήματα & Δεξιότητες (μέσω university.courses) ===
        for course in university.courses:
            if course.lesson_name:
                profile["courses"].append(course.lesson_name.strip())

            for cs in course.skills:
                if getattr(cs, "skill", None):
                    esco_id = cs.skill.esco_id or "N/A"
                    skill_name = (cs.skill.skill_name or "").strip()
                    if skill_name:
                        # 1. ESCO Label για similarity
                        esco_label = f"{skill_name} (ESCO: {esco_id})"
                        profile["skills"].add(esco_label)
                        # 2. Απλό όνομα για εμφάνιση
                        profile["skills_raw_names"].add(skill_name)


        # === Τίτλοι πτυχίων (μέσω university.programs) ===
        for program in university.programs:
            titles = program.degree_titles
            if not titles:
                continue
            
            if isinstance(titles, str):
                try:
                    titles = json.loads(titles)
                except Exception:
                    titles = [titles]
            
            # Διόρθωση: Εξασφάλιση ότι το titles είναι iterable
            if not isinstance(titles, list):
                titles = [titles]

            try:
                for title in titles:
                    if not title: continue
                    clean_title = re.sub(r"[^a-zA-Z0-9 \-&]", "", str(title)).strip()
                    if clean_title:
                        profile["degrees"].add(clean_title)
            except Exception: # Πιθανό TypeError αν το titles δεν είναι σωστά format
                 pass

        profile["skills"] = sorted(profile["skills"])
        profile["skills_raw_names"] = sorted(list(profile["skills_raw_names"]))
        profile["courses"] = sorted(list({c for c in profile["courses"] if c}))
        profile["degrees"] = sorted(profile["degrees"])
        
        self._profile_cache[university_id] = profile
        return profile


    # ------------------------------
    # Similarity: combined (Παραμένει ως είχε)
    # ------------------------------
    def find_similar_universities(self, target_univ_id: int, top_n: int = 5) -> List[Dict[str, Any]]:
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
    # Helper: Get Degree-Skill Similarity (Παραμένει ως είχε)
    # ------------------------------
    def _get_degree_skills_similarity(self, similar_univ_ids: List[int], target_degree: str, target_skills_raw: set) -> List[Dict[str, Any]]:
        degree_texts = []
        
        for univ_id in similar_univ_ids:
            p = self.build_university_profile(univ_id)
            if not p or target_degree not in p["degrees"]:
                continue
            skill_text = " ".join(p["skills_raw_names"]) 
            if skill_text:
                degree_texts.append(skill_text)

        if not degree_texts:
            return []
        
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(degree_texts) 
        feature_names = vectorizer.get_feature_names_out()
        
        avg_weights = vectors.mean(axis=0).A1
        
        ranked_skills = []
        for i, skill_name_raw in enumerate(feature_names):
            skill_weight = avg_weights[i]
            if skill_name_raw.capitalize() in target_skills_raw: # Έλεγχος με capitalize
                continue 
                
            ranked_skills.append({
                "skill_name": skill_name_raw.capitalize(),
                "skill_score": skill_weight 
            })

        if not ranked_skills:
            return []
            
        max_score = max(s['skill_score'] for s in ranked_skills)
        if max_score > 0:
            for s in ranked_skills:
                s['skill_score'] = round(s['skill_score'] / max_score, 3)
        else:
            return []
            
        ranked_skills = sorted(ranked_skills, key=lambda x: x['skill_score'], reverse=True)
        return ranked_skills[:5]


    # ------------------------------
    # Suggest degrees with skills (Παραμένει ως είχε)
    # ------------------------------
    def suggest_degrees_with_skills(self, target_univ_id: int, top_n: int = 5):
        similar_univs = self.find_similar_universities(target_univ_id, top_n=10)
        target_profile = self.build_university_profile(target_univ_id)
        if not similar_univs or not target_profile:
            return []

        similar_univ_ids = [u["university_id"] for u in similar_univs] 
        target_skills_raw = set(target_profile["skills_raw_names"]) 
        target_degrees = set(target_profile["degrees"])
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
            new_skills = set(p["skills"]) - set(target_profile["skills"])
            combined_text = " ".join(p["skills"] + p["courses"])

            for deg in new_degrees:
                degree_freq[deg] += 1
                degree_texts[deg] = degree_texts.get(deg, "") + " " + combined_text
                overlap = len(set(p["skills"]) & set(target_profile["skills"]))
                compat = overlap / (len(p["skills"]) + 1)
                degree_compat[deg] += compat
                degree_skill_bonus[deg] += len(new_skills)

        if not degree_texts:
            return [] 

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
            
            deg_lower = deg.lower()
            if 'master' in deg_lower or 'msc' in deg_lower or 'ma' in deg_lower:
                degree_type = 'MSc/MA'
            elif 'phd' in deg_lower or 'doctorate' in deg_lower:
                degree_type = 'PhD'
            else:
                degree_type = 'BSc/BA'

            top_skills = self._get_degree_skills_similarity(
                similar_univ_ids, 
                deg, 
                target_skills_raw
            )
            
            final.append({
                "degree": deg, 
                "score": round(total_score, 3), 
                "top_skills": top_skills,
                "degree_type": degree_type,
            })

        final = sorted(final, key=lambda x: x['score'], reverse=True)
        return final[:top_n]