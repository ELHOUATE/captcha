# ============================================
# database.py — Connexion MySQL avec SQLAlchemy
# ============================================

from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

# ── Configuration ──────────────────────────────────────────────────────────────
DATABASE_URL = "mysql+pymysql://root:motdepasse@localhost/captcha_db"
# Change "root" et "motdepasse" par tes identifiants MySQL

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


# ── Modèles SQLAlchemy (miroir des tables MySQL) ───────────────────────────────

class Classe(Base):
    __tablename__ = "classes"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    nom        = Column(String(50), nullable=False, unique=True)
    label_fr   = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    images     = relationship("Image", back_populates="classe")


class Image(Base):
    __tablename__ = "images"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    classe_id       = Column(Integer, ForeignKey("classes.id"), nullable=False)
    chemin          = Column(String(255), nullable=False)
    contient_objet  = Column(Boolean, nullable=False)
    confiance_yolo  = Column(Float, default=0.0)
    nb_objets       = Column(Integer, default=0)
    created_at      = Column(DateTime, default=datetime.utcnow)
    classe          = relationship("Classe", back_populates="images")


class Session(Base):
    __tablename__ = "sessions"
    token      = Column(String(36), primary_key=True)
    classe_id  = Column(Integer, ForeignKey("classes.id"), nullable=False)
    image_ids  = Column(JSON, nullable=False)
    correctes  = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    utilise    = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Tentative(Base):
    __tablename__ = "tentatives"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    token      = Column(String(36))
    succes     = Column(Boolean, nullable=False)
    score      = Column(Float, nullable=False)
    ip         = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Utilitaire ─────────────────────────────────────────────────────────────────

def get_db():
    """Générateur de session DB — utilisé dans les routes FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()