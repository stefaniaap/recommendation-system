# backend/core.py
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
from backend.models import University
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import json
import re
import logging
import math

logger = logging.getLogger(__name__)

class UniversityRecommender:
    """
    University recommender system for suggesting similar universities and
    recommending degree programs with enriched skill sets.
    """

    def __init__(self, db: Session, weights: Optional[Dict[str, float]] = None, cache_enabled: bool = True):
        self.db = db
        self._profile_cache: Dict[int, Dict[str, Any]] = {}
        self.cache_enabled = cache_enabled

        # UPDATED WEIGHTS - Reduced novelty, increased compatibility
        default = {
            "frequency": 0.35,
            "novelty": 0.15,
            "compatibility": 0.30,
            "skill_enrichment": 0.20,
        }

        if weights:
            merged = default.copy()
            merged.update(weights)
            total = sum(merged.values())
            if total == 0:
                logger.warning("Provided weights sum to 0. Reverting to defaults.")
                merged = default
            else:
                merged = {k: v / total for k, v in merged.items()}
            self.weights = merged
        else:
            self.weights = default

    # -------------------------------------------------------------------------
    # Build university profile
    # -------------------------------------------------------------------------
    def build_university_profile(self, university_id: int) -> Optional[Dict[str, Any]]:
        if self.cache_enabled and university_id in self._profile_cache:
            return self._profile_cache[university_id]

        university = self.db.query(University).filter_by(university_id=university_id).first()
        if not university:
            return None

        profile = {
            "skills": set(), 
            "skills_raw_names": set(), 
            "courses": [], 
            "degrees": set(),
            "program_skills": defaultdict(set)
        }

        for program in getattr(university, "programs", []) or []:
            titles = getattr(program, "degree_titles", None)
            if not titles:
                continue

            if isinstance(titles, str):
                try:
                    titles = json.loads(titles)
                except Exception:
                    titles = [titles]
            if not isinstance(titles, list):
                titles = [titles]

            clean_program_titles = []
            for title in titles:
                if not title: continue
                clean_title = re.sub(r"[^a-zA-Z0-9 \-&]", "", str(title)).strip()
                if clean_title:
                    profile["degrees"].add(clean_title)
                    clean_program_titles.append(clean_title)

            for course in getattr(program, "courses", []) or []:
                lesson_name = getattr(course, "lesson_name", None)
                if lesson_name:
                    profile["courses"].append(lesson_name.strip())

                for cs in getattr(course, "skills", []) or []:
                    skill_obj = getattr(cs, "skill", None)
                    if skill_obj:
                        skill_name = (getattr(skill_obj, "skill_name", "") or "").strip()
                        if skill_name:
                            profile["skills"].add(skill_name)
                            profile["skills_raw_names"].add(skill_name)
                            for cpt in clean_program_titles:
                                profile["program_skills"][cpt].add(skill_name)

        profile["skills"] = sorted(list(profile["skills"]))
        profile["skills_raw_names"] = sorted(list(profile["skills_raw_names"]))
        profile["courses"] = sorted(list({c for c in profile["courses"] if c}))
        profile["degrees"] = sorted(list(profile["degrees"]))
        profile["program_skills"] = {k: sorted(list(v)) for k, v in profile["program_skills"].items()}

        if self.cache_enabled:
            self._profile_cache[university_id] = profile

        return profile

    # -------------------------------------------------------------------------
    # Similar universities
    # -------------------------------------------------------------------------
    def find_similar_universities(self, target_univ_id: int, top_n: int = 5) -> List[Dict[str, Any]]:
        target_profile = self.build_university_profile(target_univ_id)
        if not target_profile:
            return []

        all_univs = self.db.query(University).filter(University.university_id != target_univ_id).all()
        docs, valid_univs = [], []

        for u in all_univs:
            p = self.build_university_profile(getattr(u, "university_id"))
            if not p:
                continue
            combined_text = " ".join(p["skills"] + p["courses"] + p["degrees"]).strip()
            if combined_text:
                docs.append(combined_text)
                valid_univs.append(u)

        if not docs:
            return []

        target_text = " ".join(target_profile["skills"] + target_profile["courses"] + target_profile["degrees"]).strip()

        try:
            vectorizer = TfidfVectorizer()
            vectors = vectorizer.fit_transform(docs + [target_text])
            sims = cosine_similarity(vectors[-1], vectors[:-1]).flatten()
        except Exception as e:
            logger.exception("Error computing similarity for universities: %s", e)
            return []

        ranked = sorted(zip(valid_univs, sims), key=lambda x: x[1], reverse=True)[:top_n]
        return [
            {
                "university_id": getattr(u, "university_id"),
                "name": getattr(u, "university_name", "Unknown"),
                "country": getattr(u, "country", "Unknown"),
                "similarity_score": round(float(score), 4),
            }
            for u, score in ranked
        ]

    # -------------------------------------------------------------------------
    # Degree skills similarity
    # -------------------------------------------------------------------------
    def _get_degree_skills_similarity(self, similar_univ_ids: List[int], target_degree: str, target_skills_raw: Set[str]) -> List[Dict[str, Any]]:
        skill_counter = defaultdict(int)
        all_skills = []
        target_skills_lc = {s.lower() for s in target_skills_raw}

        for univ_id in similar_univ_ids:
            profile = self.build_university_profile(univ_id)
            if not profile or target_degree not in profile["degrees"]:
                continue
            
            degree_specific_skills = profile.get("program_skills", {}).get(target_degree, [])
            filtered = [s for s in degree_specific_skills if s.lower() not in target_skills_lc]
            
            all_skills.extend(filtered)
            for skill in filtered:
                skill_counter[skill.strip()] += 1

        if not skill_counter:
            return []

        try:
            vectorizer = TfidfVectorizer(lowercase=True)
            vectors = vectorizer.fit_transform([" ".join(all_skills)])
            weights = dict(zip(vectorizer.get_feature_names_out(), vectors.toarray()[0]))
        except Exception:
            weights = {}

        max_count = max(skill_counter.values())
        raw_scores = []
        for skill, count in skill_counter.items():
            base_score = count / max_count
            tfidf_weight = weights.get(skill.lower(), 0.1)
            combined = 0.5 * base_score + 0.5 * tfidf_weight
            raw_scores.append((skill, combined))

        min_s = min(v for _, v in raw_scores)
        max_s = max(v for _, v in raw_scores)
        spread = max(max_s - min_s, 0.001)

        ranked_skills = []
        for skill, val in raw_scores:
            normalized = (val - min_s) / spread
            boosted = math.pow(normalized, 1.2) 
            final_score = round(0.2 + 0.75 * boosted, 3)
            ranked_skills.append({"skill_name": skill, "skill_score": final_score})

        ranked_skills.sort(key=lambda x: x["skill_score"], reverse=True)
        return ranked_skills[:5]

    # -------------------------------------------------------------------------
    # Suggest degrees with improved filtering
    # -------------------------------------------------------------------------
    def suggest_degrees_with_skills(self, target_univ_id: int, top_n: int = 5) -> List[Dict[str, Any]]:
        similar_univs = self.find_similar_universities(target_univ_id, top_n=10)
        target_profile = self.build_university_profile(target_univ_id)

        if not target_profile or not similar_univs:
            return []

        similar_univ_ids = [u["university_id"] for u in similar_univs]
        target_skills_raw = set(target_profile["skills_raw_names"])
        target_degrees = set(target_profile["degrees"])
        target_text = " ".join(target_profile["skills"] + target_profile["courses"] + target_profile["degrees"])

        # NEW: Minimum skill overlap threshold
        MIN_SKILL_OVERLAP = 0.10  # At least 10% common skills

        degree_texts, degree_freq, degree_compat, degree_skill_bonus = {}, defaultdict(int), defaultdict(float), defaultdict(int)

        for u in similar_univs:
            p = self.build_university_profile(u["university_id"])
            if not p:
                continue

            new_degrees = set(p["degrees"]) - target_degrees
            new_skills = set(p["skills"]) - set(target_profile["skills"])
            combined_text = " ".join(p["skills"] + p["courses"])

            for deg in new_degrees:
                p_skills_raw = {s.lower() for s in p["skills_raw_names"]}
                target_skills_lc = {s.lower() for s in target_profile["skills_raw_names"]}
                overlap = len(p_skills_raw & target_skills_lc)
                union_count = len(p_skills_raw | target_skills_lc)
                
                # NEW: Skip degrees with very low overlap (filters out Law, etc.)
                compat = overlap / (union_count + 1)
                if compat < MIN_SKILL_OVERLAP:
                    continue
                
                degree_freq[deg] += 1
                degree_texts[deg] = degree_texts.get(deg, "") + " " + combined_text
                degree_compat[deg] += compat
                degree_skill_bonus[deg] += len(new_skills)

        if not degree_texts:
            return []

        degrees = list(degree_texts.keys())
        docs = [degree_texts[d] for d in degrees] + [target_text]

        try:
            vectorizer = TfidfVectorizer()
            vectors = vectorizer.fit_transform(docs)
            sims = cosine_similarity(vectors[-1], vectors[:-1]).flatten()
        except Exception as e:
            logger.exception("Error computing degree similarities: %s", e)
            sims = [0.0] * len(degrees)

        final = []
        max_freq = max(degree_freq.values()) if degree_freq else 1
        max_skill_bonus = max(degree_skill_bonus.values()) if degree_skill_bonus else 1

        for i, deg in enumerate(degrees):
            freq_score = degree_freq[deg] / max_freq
            
            # NEW: Sigmoid-based novelty (less extreme)
            sim_val = float(sims[i])
            novelty_score = 1.0 / (1.0 + math.exp(-5 * (1.0 - sim_val - 0.5)))
            
            compat_score = degree_compat[deg] / degree_freq[deg]
            skill_enrichment_score = degree_skill_bonus[deg] / max_skill_bonus

            total_score = (
                self.weights["frequency"] * freq_score +
                self.weights["novelty"] * novelty_score +
                self.weights["compatibility"] * compat_score +
                self.weights["skill_enrichment"] * skill_enrichment_score
            )

            deg_lower = deg.lower()
            if re.search(r'\b(master|msc|ma|m\.sc|msc)\b', deg_lower):
                degree_type = 'MSc/MA'
            elif re.search(r'\b(phd|doctorate|doctoral)\b', deg_lower):
                degree_type = 'PhD'
            else:
                degree_type = 'BSc/BA'

            top_skills = self._get_degree_skills_similarity(similar_univ_ids, deg, target_skills_raw)

            final.append({
                "degree": deg,
                "score": round(total_score, 3),
                "degree_type": degree_type,
                "top_skills": top_skills,
                "metrics": {
                    "frequency": round(freq_score, 2),
                    "compatibility": round(compat_score, 2),
                    "novelty": round(novelty_score, 2),
                    "skill_enrichment": round(skill_enrichment_score * 100)
                }
            })

        return sorted(final, key=lambda x: x['score'], reverse=True)[:top_n]
    