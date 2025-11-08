# backend/core.py (Ολοκληρωμένο, με βελτιώσεις)
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
from backend.models import University
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import json
import re
import logging

logger = logging.getLogger(__name__)


class UniversityRecommender:
    """
    Recommender class για προτάσεις πτυχίων/skills βασισμένο σε TF-IDF + cosine similarity.
    Βελτιώσεις:
     - Jaccard-like compatibility
     - case-insensitive skill matching
     - configurable weights για scoring
     - πιο ασφαλής extra χειρισμός edge-cases
    """

    def __init__(
        self,
        db: Session,
        weights: Optional[Dict[str, float]] = None,
        cache_enabled: bool = True,
    ):
        """
        Args:
            db: SQLAlchemy session
            weights: dict με βάρη για τα metrics (default αν δεν δοθούν)
                example: {
                    "frequency": 0.30,
                    "novelty": 0.25,
                    "compatibility": 0.20,
                    "skill_enrichment": 0.15
                }
            cache_enabled: αν ενεργοποιείται το cache προφίλ
        """
        self.db = db
        self._profile_cache: Dict[int, Dict[str, Any]] = {}
        self.cache_enabled = cache_enabled

        # default weights (προσπάθησα να κρατήσω τη λογική που είχες)
        default = {
            "frequency": 0.30,
            "novelty": 0.25,
            "compatibility": 0.20,
            "skill_enrichment": 0.15,
        }
        if weights:
            # merge με defaults ώστε να μην λείψει κάποιο πεδίο
            merged = default.copy()
            merged.update(weights)
            total = sum(merged.values())
            if total == 0:
                logger.warning("Total of provided weights is 0; falling back to defaults.")
                merged = default
            else:
                # normalize ώστε τα βάρη να αθροίζουν 1.0
                merged = {k: v / total for k, v in merged.items()}
            self.weights = merged
        else:
            self.weights = default

    # ------------------------------
    # Build university profile
    # ------------------------------
    def build_university_profile(self, university_id: int) -> Optional[Dict[str, Any]]:
        """Επιστρέφει ένα προφίλ του πανεπιστημίου (skills, raw skill names, courses, degrees)."""
        if self.cache_enabled and university_id in self._profile_cache:
            return self._profile_cache[university_id]

        university = self.db.query(University).filter_by(university_id=university_id).first()
        if not university:
            return None

        profile = {
            "skills": set(),  # formatted skills (με ESCO id αν υπάρχει)
            "skills_raw_names": set(),  # μόνο ονόματα skills (για matching)
            "courses": [],  # list of course names
            "degrees": set(),  # set of degree titles (cleaned)
        }

        # === Μαθήματα & Δεξιότητες ===
        for course in getattr(university, "courses", []) or []:
            lesson_name = getattr(course, "lesson_name", None)
            if lesson_name:
                profile["courses"].append(lesson_name.strip())
            # υποθέτουμε ότι course.skills είναι collection από αντικείμενα που έχουν cs.skill.skill_name κτλ.
            for cs in getattr(course, "skills", []) or []:
                skill_obj = getattr(cs, "skill", None)
                if skill_obj:
                    esco_id = getattr(skill_obj, "esco_id", None) or "N/A"
                    skill_name = (getattr(skill_obj, "skill_name", "") or "").strip()
                    if skill_name:
                        profile["skills"].add(f"{skill_name} (ESCO: {esco_id})")
                        profile["skills_raw_names"].add(skill_name)

        # === Τίτλοι πτυχίων ===
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
            for title in titles:
                if not title:
                    continue
                # καθαρισμός τίτλου: κρατάμε αριθμούς, γράμματα, - & &
                clean_title = re.sub(r"[^a-zA-Z0-9 \-&]", "", str(title)).strip()
                if clean_title:
                    profile["degrees"].add(clean_title)

        # μετατροπές σε sorted lists (για determinism)
        profile["skills"] = sorted(profile["skills"])
        profile["skills_raw_names"] = sorted(list({s for s in profile["skills_raw_names"] if s}))
        profile["courses"] = sorted(list({c for c in profile["courses"] if c}))
        profile["degrees"] = sorted(profile["degrees"])

        if self.cache_enabled:
            self._profile_cache[university_id] = profile

        return profile

    # ------------------------------
    # Find similar universities
    # ------------------------------
    def find_similar_universities(self, target_univ_id: int, top_n: int = 5) -> List[Dict[str, Any]]:
        """Επιστρέφει λίστα από παρόμοια πανεπιστήμια (με similarity score)."""
        target_profile = self.build_university_profile(target_univ_id)
        if not target_profile:
            return []

        all_univs = self.db.query(University).filter(University.university_id != target_univ_id).all()

        docs: List[str] = []
        valid_univs: List[University] = []
        for u in all_univs:
            p = self.build_university_profile(getattr(u, "university_id"))
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

    # ------------------------------
    # Helper: Get Degree-Skill Similarity
    # ------------------------------
    def _get_degree_skills_similarity(
        self, similar_univ_ids: List[int], target_degree: str, target_skills_raw: Set[str]
    ) -> List[Dict[str, Any]]:
        """
        Επιστρέφει top skills που εμφανίζονται σε πανεπιστήμια που έχουν / το ίδιο degree.
        Αποφεύγει να προτείνει skills που ήδη υπάρχουν στο target (case-insensitive).
        """
        degree_texts: List[str] = []
        for univ_id in similar_univ_ids:
            p = self.build_university_profile(univ_id)
            if not p:
                continue
            # μόνο πανεπιστήμια που περιέχουν τον συγκεκριμένο τίτλο
            if target_degree not in p["degrees"]:
                continue
            # χρησιμοποιούμε raw skill names για να επεξεργαστούμε tokens
            skill_text = " ".join(p["skills_raw_names"])
            if skill_text:
                degree_texts.append(skill_text)

        if not degree_texts:
            return []

        try:
            vectorizer = TfidfVectorizer(
    analyzer='word',
    ngram_range=(1, 2),  # κρατάει και μονο- και διπλές λέξεις
    token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b",  # σωστός χειρισμός λέξεων
    lowercase=True
)


            vectors = vectorizer.fit_transform(degree_texts)
            feature_names = vectorizer.get_feature_names_out()  # lowercased tokens
            avg_weights = vectors.mean(axis=0).A1  # numpy array
        except Exception as e:
            logger.exception("Error in _get_degree_skills_similarity: %s", e)
            return []

        # prepare lower-case set για σύγκριση
        target_skills_lc = {s.lower() for s in target_skills_raw}

        ranked_skills = []
        for i, token in enumerate(feature_names):
            token_lc = token.lower()
            # skip αν ήδη υπάρχει στο target (case-insensitive)
            if token_lc in target_skills_lc:
                continue
            weight = float(avg_weights[i])
            if weight > 0:
                ranked_skills.append({
                    "skill_name": token.capitalize(),  # παρουσιάζουμε με αρχικό κεφαλαίο
                    "skill_score": weight
                })

        if not ranked_skills:
            return []

        max_score = max(s['skill_score'] for s in ranked_skills)
        if max_score <= 0:
            return []

        # κανονικοποίηση σε 0..1 (τρυπ. 3 δεξιότητες top-return)
        for s in ranked_skills:
            s['skill_score'] = round(s['skill_score'] / max_score, 3)

        return sorted(ranked_skills, key=lambda x: x['skill_score'], reverse=True)[:5]

    # ------------------------------
    # Suggest degrees with skills + metrics
    # ------------------------------
    def suggest_degrees_with_skills(self, target_univ_id: int, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Προτείνει νέα degrees για το target_univ_id βασισμένο σε παρόμοια πανεπιστήμια.
        Επιστρέφει λίστα από dicts: degree, score, degree_type, top_skills, metrics.
        """
        similar_univs = self.find_similar_universities(target_univ_id, top_n=10)
        target_profile = self.build_university_profile(target_univ_id)
        if not target_profile:
            return []

        if not similar_univs:
            # fallback: αν δεν βρέθηκαν παρόμοια πανεπιστήμια, δεν προτείνουμε τίποτα
            return []

        similar_univ_ids = [u["university_id"] for u in similar_univs]
        target_skills_raw = set(target_profile["skills_raw_names"])
        target_degrees = set(target_profile["degrees"])
        target_text = " ".join(target_profile["skills"] + target_profile["courses"] + target_profile["degrees"])

        degree_texts: Dict[str, str] = {}
        degree_freq: Dict[str, int] = defaultdict(int)
        degree_compat: Dict[str, float] = defaultdict(float)
        degree_skill_bonus: Dict[str, int] = defaultdict(int)

        for u in similar_univs:
            p = self.build_university_profile(u["university_id"])
            if not p:
                continue

            # degrees που υπάρχουν σε παρόμοια univs αλλά όχι στο target
            new_degrees = set(p["degrees"]) - target_degrees
            # νέες δεξιότητες (με τη μορφή "Skill (ESCO: id)") σε σχέση με target
            new_skills = set(p["skills"]) - set(target_profile["skills"])
            combined_text = " ".join(p["skills"] + p["courses"])

            for deg in new_degrees:
                degree_freq[deg] += 1
                degree_texts[deg] = degree_texts.get(deg, "") + " " + combined_text

                # Compatibility: Jaccard-like ratio per occurrence
                # overlap = κοινά skills μεταξύ p και target, αλλά χρησιμοποιούμε raw names σύγκριση
                p_skills_raw = {s.lower() for s in p["skills_raw_names"]}
                target_skills_lc = {s.lower() for s in target_profile["skills_raw_names"]}
                overlap = len(p_skills_raw & target_skills_lc)
                union_count = len(p_skills_raw | target_skills_lc)
                # προσθέτουμε +1 στο παρονομαστή για να αποφύγουμε division by zero
                compat = overlap / (union_count + 1)
                degree_compat[deg] += compat

                # Πόσες "νέες" δεξιότητες φέρνει (count)
                degree_skill_bonus[deg] += len(new_skills)

        if not degree_texts:
            return []

        degrees = list(degree_texts.keys())
        docs = [degree_texts[d] for d in degrees] + [target_text]

        try:
            vectorizer = TfidfVectorizer()
            vectors = vectorizer.fit_transform(docs)
            # similarity target -> degrees
            sims = cosine_similarity(vectors[-1], vectors[:-1]).flatten()
        except Exception as e:
            logger.exception("Error computing degree similarities: %s", e)
            sims = [0.0] * len(degrees)

        final: List[Dict[str, Any]] = []

        max_freq = max(degree_freq.values()) if degree_freq else 1
        max_skill_bonus = max(degree_skill_bonus.values()) if degree_skill_bonus else 1

        for i, deg in enumerate(degrees):
            freq_score = degree_freq[deg] / max_freq if max_freq > 0 else 0.0
            novelty_score = max(0.0, min(1.0, 1.0 - float(sims[i])))  # bounded 0..1
            compat_score = (degree_compat[deg] / degree_freq[deg]) if degree_freq[deg] > 0 else 0.0
            skill_enrichment_score = degree_skill_bonus[deg] / max_skill_bonus if max_skill_bonus > 0 else 0.0

            # compute weighted total score (με τα βάρη που έχουμε στο self.weights)
            total_score = (
                self.weights.get("frequency", 0.0) * freq_score
                + self.weights.get("novelty", 0.0) * novelty_score
                + self.weights.get("compatibility", 0.0) * compat_score
                + self.weights.get("skill_enrichment", 0.0) * skill_enrichment_score
            )

            deg_lower = deg.lower()
            # πιο αυστηρός regex-based classification (word boundaries)
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
                    "frequency": round(freq_score * 100),
                    # round compatibility to percentage (0..100)
                    "compatibility": round(compat_score * 100),
                    "skill_enrichment": int(degree_skill_bonus[deg]),
                    "novelty": round(novelty_score * 100)
                }
            })

        # ταξινόμηση κατά score (φθίνουσα)
        sorted_final = sorted(final, key=lambda x: x['score'], reverse=True)[:top_n]
        return sorted_final
