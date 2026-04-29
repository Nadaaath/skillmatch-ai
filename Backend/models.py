from sqlalchemy import Column, Integer, String, Float, Text
from database import Base


# =========================
# CANDIDATE MODEL
# =========================
class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)

    experience_years = Column(Float, default=0.0)
    soft_skill_score = Column(Float, default=3.0)

    technical_skills = Column(Text)   # comma-separated
    cv_text = Column(Text)


# =========================
# JOB MODEL
# =========================
class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)

    required_skills = Column(Text)  # comma-separated
