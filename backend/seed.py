from sqlalchemy.orm import Session
from backend.database import SessionLocal, init_db
from backend.models import University, DegreeProgram, Course, Skill, CourseSkill, Occupation, SkillOccupation

def run_seed():
    init_db()
    db: Session = SessionLocal()

    try:
        u1 = University(university_id=1, university_name="Aristotle University of Thessaloniki", country="Greece")
        u2 = University(university_id=2, university_name="National and Kapodistrian University of Athens", country="Greece")
        u3 = University(university_id=3, university_name="University of Patras", country="Greece")
        u4 = University(university_id=4, university_name="Technical University of Munich", country="Germany")
        u5 = University(university_id=5, university_name="Politecnico di Milano", country="Italy")
        for u in [u1, u2, u3, u4, u5]:
            db.merge(u)

        p11 = DegreeProgram(program_id=11, university_id=1, degree_type="BSc", degree_titles=["Computer Science"], language="English", duration_semesters="8", total_ects="240")
        p12 = DegreeProgram(program_id=12, university_id=1, degree_type="MSc", degree_titles=["Data Science"], language="English", duration_semesters="4", total_ects="120")
        p21 = DegreeProgram(program_id=21, university_id=2, degree_type="BSc", degree_titles=["Informatics"], language="Greek", duration_semesters="8", total_ects="240")
        p22 = DegreeProgram(program_id=22, university_id=2, degree_type="MSc", degree_titles=["Artificial Intelligence"], language="English", duration_semesters="4", total_ects="120")
        p31 = DegreeProgram(program_id=31, university_id=3, degree_type="BSc", degree_titles=["Electrical & Computer Engineering"], language="Greek", duration_semesters="10", total_ects="300")
        p32 = DegreeProgram(program_id=32, university_id=3, degree_type="MSc", degree_titles=["Software Engineering"], language="English", duration_semesters="4", total_ects="120")
        p41 = DegreeProgram(program_id=41, university_id=4, degree_type="BSc", degree_titles=["Informatics"], language="English", duration_semesters="6", total_ects="180")
        p42 = DegreeProgram(program_id=42, university_id=4, degree_type="MSc", degree_titles=["Robotics, Cognition, Intelligence"], language="English", duration_semesters="4", total_ects="120")
        p51 = DegreeProgram(program_id=51, university_id=5, degree_type="BSc", degree_titles=["Computer Engineering"], language="English", duration_semesters="6", total_ects="180")
        p52 = DegreeProgram(program_id=52, university_id=5, degree_type="MSc", degree_titles=["Machine Learning & AI"], language="English", duration_semesters="4", total_ects="120")
        for p in [p11,p12,p21,p22,p31,p32,p41,p42,p51,p52]:
            db.merge(p)

        courses = [
            Course(course_id=1001, university_id=1, program_id=11, lesson_name="Programming I", description="Python intro"),
            Course(course_id=1003, university_id=1, program_id=11, lesson_name="Data Structures", description="DSA"),
            Course(course_id=1011, university_id=1, program_id=12, lesson_name="Machine Learning", description="ML core"),
            Course(course_id=2002, university_id=2, program_id=21, lesson_name="Algorithms", description="Design & analysis"),
            Course(course_id=2013, university_id=2, program_id=22, lesson_name="Computer Vision", description="CNNs & vision"),
            Course(course_id=3014, university_id=3, program_id=32, lesson_name="Distributed Systems", description="Consistency & consensus"),
            Course(course_id=4005, university_id=4, program_id=41, lesson_name="Parallel Computing", description="Threads, MPI, GPU"),
            Course(course_id=4011, university_id=4, program_id=42, lesson_name="Robotics I", description="Kinematics & control"),
            Course(course_id=5013, university_id=5, program_id=52, lesson_name="Recommender Systems", description="CF & content-based"),
        ]
        for c in courses:
            db.merge(c)

        skills = [
            Skill(skill_id=1,  skill_name="Python",            skill_url="https://esco.example/python",            esco_id="ESCO:PY",  esco_level="4"),
            Skill(skill_id=4,  skill_name="Data Structures",   skill_url="https://esco.example/data-structures",   esco_id="ESCO:DS",  esco_level="5"),
            Skill(skill_id=5,  skill_name="Algorithms",        skill_url="https://esco.example/algorithms",        esco_id="ESCO:ALG", esco_level="5"),
            Skill(skill_id=10, skill_name="Machine Learning",  skill_url="https://esco.example/ml",                esco_id="ESCO:ML",  esco_level="6"),
            Skill(skill_id=13, skill_name="Computer Vision",   skill_url="https://esco.example/cv",                esco_id="ESCO:CV",  esco_level="6"),
            Skill(skill_id=14, skill_name="Distributed Systems", skill_url="https://esco.example/distributed",     esco_id="ESCO:DSYS", esco_level="5"),
            Skill(skill_id=18, skill_name="Robotics",          skill_url="https://esco.example/robotics",          esco_id="ESCO:ROB", esco_level="6"),
        ]
        for s in skills:
            db.merge(s)

        links = [
            CourseSkill(course_id=1001, skill_id=1,  categories=["programming", "python basics"]),
            CourseSkill(course_id=1003, skill_id=4,  categories=["data structures", "theory"]),
            CourseSkill(course_id=2002, skill_id=5,  categories=["algorithms", "analysis"]),
            CourseSkill(course_id=1011, skill_id=10, categories=["ml", "supervised"]),
            CourseSkill(course_id=2013, skill_id=13, categories=["cv", "deep learning"]),
            CourseSkill(course_id=3014, skill_id=14, categories=["distributed", "consensus"]),
            CourseSkill(course_id=4011, skill_id=18, categories=["robotics", "kinematics"]),
            CourseSkill(course_id=5013, skill_id=10, categories=["recommenders", "ml"]),
        ]
        for l in links:
            db.merge(l)

        occs = [
            Occupation(occupation_id="O-001", occupation_name="Data Scientist", occupation_url="https://esco.example/occupations/data-scientist", esco_code="1234.1"),
            Occupation(occupation_id="O-002", occupation_name="Software Engineer", occupation_url="https://esco.example/occupations/software-engineer", esco_code="2512.0"),
            Occupation(occupation_id="O-003", occupation_name="ML Engineer", occupation_url="https://esco.example/occupations/ml-engineer", esco_code="2511.5"),
        ]
        for o in occs:
            db.merge(o)

        so = [
            SkillOccupation(skill_id=10, occupation_id="O-001"),
            SkillOccupation(skill_id=5,  occupation_id="O-002"),
            SkillOccupation(skill_id=14, occupation_id="O-002"),
            SkillOccupation(skill_id=10, occupation_id="O-003"),
        ]
        for x in so:
            db.merge(x)

        db.commit()
        print("Seed complete.")
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
