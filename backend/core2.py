from collections import defaultdict
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
# Υποθέτουμε ότι αυτά τα models είναι σωστά ορισμένα
from backend.models import University, Course 
import json
import re

class CourseRecommender:
    """Recommender για προτάσεις μαθημάτων και πτυχίων ανά πανεπιστήμιο."""

    def __init__(self, db: Session):
        self.db = db

    # ==========================================================
    # 🔹 Βοηθητικές μέθοδοι (Helper Methods)
    # ==========================================================
    def get_university(self, univ_id: int) -> Optional[University]:
        """Επιστρέφει αντικείμενο University από τη βάση."""
        return self.db.query(University).filter_by(university_id=univ_id).first()

    def get_all_universities(self) -> List[University]:
        """Επιστρέφει όλα τα πανεπιστήμια από τη βάση."""
        return self.db.query(University).all()
    
    @staticmethod
    def normalize_name(name: str) -> str:
        """Αφαιρεί κενά, σημεία στίξης, και μετατρέπει σε κεφαλαία για ασφαλή σύγκριση."""
        if not name:
            return ""
        # Περιλαμβάνουμε Ελληνικούς χαρακτήρες
        cleaned_name = re.sub(r'[^a-zA-Z0-9\s\u0370-\u03FF\u1F00-\u1FFF]', '', name)
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
        # Καθαρισμός, επιτρέποντας Ελληνικούς χαρακτήρες
        return [
            re.sub(r"[^a-zA-Z0-9 \-&\u0370-\u03FF\u1F00-\u1FFF]", "", str(t)).strip()
            for t in titles if t
        ]

    def get_course_details_by_name(self, course_name: str, target_univ_id: int) -> Dict[str, str]:
        """Ανακτά Description, Objectives, κ.λπ. για ένα μάθημα από τη βάση."""
        
        # 1. Ψάξε στο πανεπιστήμιο-στόχο
        course = self.db.query(Course).filter(
            Course.lesson_name == course_name,
            Course.university_id == target_univ_id
        ).first()
        
        # 2. Αν δεν βρεθεί, ψάξε το πρώτο που υπάρχει στη βάση (ως fallback)
        if not course:
              course = self.db.query(Course).filter(
                Course.lesson_name == course_name
            ).first()

        if course:
            # Χρησιμοποιούμε getattr για ασφαλή πρόσβαση σε πιθανόν λείποντα attributes
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
        """Δημιουργεί λίστα από degree profiles για το πανεπιστήμιο."""
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

            # Συλλογή δεξιοτήτων (Skills)
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
                    "skills": skills, # Δεξιότητες του πτυχίου
                    "courses": courses, # Μαθήματα του πτυχίου
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
        """
        Επιστρέφει παρόμοια πτυχία με βάση skills + courses + degree_type.
        - Περιλαμβάνει ΠΑΝΤΑ το target vector στο fit_transform.
        - Φιλτράρει υποψήφιους χωρίς κείμενο (άδειες λίστες).
        - Αν δεν υπάρχουν έγκυροι υποψήφιοι, επιστρέφει [] χωρίς 500.
        """
        if not target_profile or not all_profiles:
            return []

        degree_type = (target_profile.get("degree_type") or "").strip()
        # Combine skills + courses for a richer representation
        target_text = " ".join(
            (target_profile.get("skills") or []) +
            (target_profile.get("courses") or [])
        ).strip()

        # Collect candidates of same degree_type but different university
        raw_candidates = [
            p for p in all_profiles
            if (p.get("degree_type") or "").strip() == degree_type
            and p.get("university_id") != target_profile.get("university_id")
        ]

        # Build candidate documents; skip empties
        cand_objs: List[Dict[str, Any]] = []
        cand_texts: List[str] = []
        for p in raw_candidates:
            text = " ".join((p.get("skills") or []) + (p.get("courses") or [])).strip()
            if text:
                cand_objs.append(p)
                cand_texts.append(text)

        # If we have no target text or no valid candidates, nothing to compare
        if not target_text or not cand_texts:
            return []

        # Fit TF-IDF on [target] + candidates, then compare target vs candidates
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform([target_text] + cand_texts)
        # vectors[0:1] -> target, vectors[1:] -> candidates
        sims = cosine_similarity(vectors[0:1], vectors[1:]).flatten()

        ranked = sorted(zip(cand_objs, sims), key=lambda x: x[1], reverse=True)
        return [p for p, _ in ranked[:top_n]]


    # ==========================================================
    # 3️⃣ Πρόταση μαθημάτων για ένα συγκεκριμένο πτυχίο (Βασικός Αλγόριθμος)
    # ==========================================================
    def suggest_courses_for_degree(
        self,
        target_degree: Dict[str, Any],
        similar_degrees: List[Dict[str, Any]],
        top_n: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Προτείνει μαθήματα για συγκεκριμένο πτυχίο με βάση τη συμβατότητα, 
        τη συχνότητα και την πρωτοτυπία (TF-IDF/Cosine Similarity).
        """
        if not target_degree or not similar_degrees:
            return [{"info": "Δεν υπάρχουν διαθέσιμα παρόμοια πτυχία για σύσταση."}]

        target_skills = set(target_degree.get("skills", []))
        target_courses = set(target_degree.get("courses", [])) # Τα μαθήματα που ήδη έχει ο στόχος

        course_freq = defaultdict(int)
        course_skills = defaultdict(set)
        
        # 1. Συγκέντρωση μαθημάτων και skills από τα παρόμοια πτυχία
        for deg in similar_degrees:
            deg_skills = set(deg.get("skills", []))
            for course in deg.get("courses", []):
                # Εξαίρεση μαθημάτων που έχει ήδη ο στόχος
                if not course or course in target_courses:
                    continue
                
                course_freq[course] += 1
                course_skills[course].update(deg_skills)

        if not course_freq:
            return [{"info": "Δεν βρέθηκαν νέα μαθήματα για πρόταση."}]

        # 2. Υπολογισμός scores (TF-IDF για Novelty)
        courses_list = list(course_freq.keys())
        course_docs = [" ".join(course_skills[c]) for c in courses_list]
        target_doc = " ".join(target_skills)
        docs = course_docs + [target_doc]
        
        vectorizer = TfidfVectorizer()
        if all(not doc.strip() for doc in docs):
             # Αν δεν υπάρχουν δεξιότητες, η σύγκριση TF-IDF αποτυγχάνει.
             # Μπορούμε να χρησιμοποιήσουμε μόνο τη συχνότητα σε αυτή την περίπτωση,
             # αλλά για συνέπεια επιστρέφουμε σφάλμα.
             return [{"info": "Η σύσταση απέτυχε λόγω έλλειψης δεξιοτήτων (skills) για σύγκριση."}]

        vectors = vectorizer.fit_transform(docs)
        # Ομοιότητα των προτεινόμενων μαθημάτων με τον στόχο
        sims = cosine_similarity(vectors[-1], vectors[:-1]).flatten()

        results = []
        max_freq = max(course_freq.values()) if course_freq else 1
        target_univ_id = target_degree["university_id"]

        # 3. Τελική Βαθμολόγηση και ανάκτηση λεπτομερειών
        for i, cname in enumerate(courses_list):
            skills = course_skills[cname]
            
            freq_score = course_freq[cname] / max_freq
            new_skills = skills - target_skills
            
            # Υπολογισμός Συμβατότητας (Jaccard Index)
            intersection_size = len(skills & target_skills)
            union_size = len(skills | target_skills)
            compat_score = intersection_size / union_size if union_size else 0.0

            novelty_score = 1.0 - sims[i] # Πρωτοτυπία (1 - Ομοιότητα)
            new_skill_score = len(new_skills) / (len(skills) + 1) # Βάρος στις νέες δεξιότητες
            
            # Παράγοντας ποινής για πολύ χαμηλή συμβατότητα
            compatibility_factor = 1.0 if compat_score >= 0.1 else 0.05 
            
            # Σταθμισμένη τελική βαθμολογία
            total_score = round(
                compatibility_factor * (
                    0.40 * freq_score +         # Συχνότητα (Δημοφιλία)
                    0.35 * compat_score +       # Συμβατότητα (Jaccard)
                    0.15 * new_skill_score +    # Εμπλουτισμός (Νέες Skills)
                    0.10 * novelty_score        # Πρωτοτυπία (TF-IDF)
                ),
                3
            )
            
            # Ανάκτηση πλήρων λεπτομερειών μαθήματος
            course_details = self.get_course_details_by_name(cname, target_univ_id)

            results.append({
                "course": cname,
                "score": total_score,
                "new_skills": sorted(list(new_skills)),
                "compatible_skills": sorted(list(skills & target_skills)),
                "description": course_details["description"],
                "objectives": course_details["objectives"],
                "learning_outcomes": course_details["learning_outcomes"],
                "course_content": course_details["course_content"],
            })

        return sorted(results, key=lambda x: x["score"], reverse=True)[:top_n]
    
    # ==========================================================
    # 4.1️⃣ Πρόταση μαθημάτων για ΥΠΑΡΧΟΝΤΑ πτυχία
    # ==========================================================
    def suggest_courses_for_existing_degrees(
        self,
        target_univ_id: int,
        all_profiles: List[Dict[str, Any]],
        top_n: int = 10
    ) -> Dict[str, Any]:
        """Προτείνει μαθήματα για κάθε υπάρχον πτυχίο του πανεπιστημίου."""
        target_profiles = self.build_degree_profiles(target_univ_id)
        if not target_profiles:
            return {"info": "Δεν βρέθηκαν υπάρχοντα πτυχία για ανάλυση."}

        suggestions = {}
        
        for target_deg in target_profiles:
            # Βρες παρόμοια πτυχία (από τη δεξαμενή)
            similar = self.find_similar_degrees(target_deg, all_profiles, top_n=5)
            if not similar:
                continue
                
            # Χρησιμοποίησε τον βασικό αλγόριθμο για σύσταση
            suggested = self.suggest_courses_for_degree(target_deg, similar, top_n)
            title = target_deg["degree_title"].strip()
            suggestions[title] = suggested

        return suggestions or {"info": "Δεν βρέθηκαν προτάσεις για τα υπάρχοντα πτυχία."}

    # ==========================================================
    # 4.2️⃣ Πρόταση Πιθανών Νέων Πτυχίων (ΔΙΟΡΘΩΜΕΝΟ)
    # ==========================================================
    def suggest_new_degree_proposals(
        self,
        target_univ_id: int,
        all_profiles: List[Dict[str, Any]],
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """Προτείνει πιθανά νέα πτυχία, χρησιμοποιώντας τον αλγόριθμο βαθμολόγησης για τα μαθήματα."""
        target_profiles = self.build_degree_profiles(target_univ_id)
        
        target_titles_normalized = {self.normalize_name(d["degree_title"]) for d in target_profiles}
        
        # Ομαδοποίησε όλα τα πτυχία ανά τίτλο (που λείπει από τον στόχο)
        candidate_groups = defaultdict(list)
        
        for d in all_profiles:
            norm_title = self.normalize_name(d["degree_title"])
            if d.get("university_id") != target_univ_id and norm_title not in target_titles_normalized:
                candidate_groups[norm_title].append(d)
                
        if not candidate_groups:
            return [{"info": "Δεν εντοπίστηκαν νέα πιθανά πτυχία."}]

        new_degree_suggestions = []
        
        for _, cand_degrees in candidate_groups.items():
            cand_title = cand_degrees[0]["degree_title"]
            cand_degree_type = cand_degrees[0]["degree_type"]

            # 1. Δημιούργησε ένα "εικονικό" προφίλ στόχο για το ΝΕΟ πτυχίο. 
            # Αυτό είναι ο συνδυασμός όλων των χαρακτηριστικών από τα παρόμοια πτυχία.
            virtual_target_skills = set()
            virtual_target_courses = set()
            
            for d in cand_degrees:
                 virtual_target_skills.update(d.get("skills", []))
                 virtual_target_courses.update(d.get("courses", []))

            # Το virtual_target_profile αντιπροσωπεύει το νέο πτυχίο (πριν την υιοθέτηση)
            virtual_target_profile = {
                "university_id": target_univ_id, 
                "degree_title": cand_title,
                "degree_type": cand_degree_type,
                # Τα skills και courses του virtual_target_profile είναι αυτά που 
                # θα φέρει το πτυχίο, οπότε ο στόχος θα τα συγκρίνει με τα ΔΙΚΑ ΤΟΥ skills.
                "skills": [], # Κενό, γιατί το πανεπιστήμιο-στόχος δεν έχει ακόμα αυτά τα skills/courses
                "courses": [],
            }
            
            # 2. Καλείται ο πλήρης αλγόριθμος βαθμολόγησης
            # target_degree: Το virtual_target_profile (που είναι κενό στα courses/skills)
            # similar_degrees: Η λίστα με όλα τα πτυχία που έχουν αυτόν τον τίτλο (προς σύσταση)
            suggested_courses = self.suggest_courses_for_degree(
                target_profiles[0] if target_profiles else virtual_target_profile, # Χρησιμοποιούμε το 1ο υπάρχον προφίλ για σύγκριση skills
                cand_degrees,   
                top_n
            )
            
            # Φίλτραρε τα μαθήματα που έχουν score > 0
            suggested_courses = [
                c for c in suggested_courses if c['score'] > 0 
            ]

            if suggested_courses:
                new_degree_suggestions.append({
                    "degree_title": cand_title,
                    "degree_type": cand_degree_type,
                    "suggested_courses": suggested_courses,
                })

        return new_degree_suggestions or [{"info": "Δεν εντοπίστηκαν νέα πιθανά πτυχία."}]


    # ==========================================================
    # 4.3️⃣ suggest_courses (MAIN FUNCTION)
    # ==========================================================
    def suggest_courses(self, target_univ_id: int, top_n: int = 10) -> Dict[str, Any]:
        """Προτείνει μαθήματα για υπάρχοντα και πιθανά νέα πτυχία."""
        all_univs = self.get_all_universities()
        all_profiles = []
        for u in all_univs:
            profiles = self.build_degree_profiles(u.university_id)
            if profiles:
                all_profiles.extend(profiles)
                
        if not all_profiles:
            return {"info": "Δεν βρέθηκαν διαθέσιμα προφίλ πτυχίων σε κανένα πανεπιστήμιο."}

        # 1. Συστάσεις για εμπλουτισμό υπαρχόντων πτυχίων
        existing_suggestions = self.suggest_courses_for_existing_degrees(
            target_univ_id,
            all_profiles,
            top_n
        )
        
        # 2. Συστάσεις για πρόταση νέων πτυχίων
        new_degree_proposals = self.suggest_new_degree_proposals(
            target_univ_id,
            all_profiles,
            top_n
        )

        return {
            "existing_degrees": existing_suggestions,
            "new_degree_proposals": new_degree_proposals,
        }