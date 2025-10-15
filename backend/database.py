# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from backend.models import Base

# ============================
# Connection string (προσαρμόστε αν χρειάζεται)
# ============================
#DATABASE_URL = "mysql+pymysql://root:2003Sept!@localhost:3306/skillcrawlfinal"
DATABASE_URL = "mysql+pymysql://root:2003Sept!@localhost:3306/recommender_test1"


# ============================
# Engine
# ============================
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# ============================
# Session factory
# ============================
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# ============================
# Δημιουργία όλων των πινάκων
# ============================
def init_db():
    """Δημιουργεί όλους τους πίνακες αν δεν υπάρχουν."""
    Base.metadata.create_all(bind=engine)

# ============================
# Dependency για FastAPI
# ============================
def get_db():
    """
    Dependency για FastAPI: παρέχει session για κάθε request και το κλείνει μετά.
    Χρήση: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
