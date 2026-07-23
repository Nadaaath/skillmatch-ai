from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), default="candidate")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(80), nullable=True)
    education = Column(Text, nullable=True)
    experience = Column(Text, nullable=True)
    cv_text = Column(Text, nullable=True)
    skills = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    matches = relationship("Match", back_populates="candidate", cascade="all, delete-orphan")

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String(160), nullable=False)
    company = Column(String(160), nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, default=list)
    location = Column(String(120), nullable=True)
    contract_type = Column(String(80), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    matches = relationship("Match", back_populates="job", cascade="all, delete-orphan")

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    score = Column(Float, nullable=False)
    skill_score = Column(Float, nullable=False)
    semantic_score = Column(Float, nullable=False)
    matched_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="matches")
    job = relationship("Job", back_populates="matches")

class AgentConversation(Base):
    __tablename__ = "agent_conversations"
    id = Column(Integer, primary_key=True, index=True)
    user_role = Column(String(30), nullable=True)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    context_type = Column(String(80), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ScrapedJob(Base):
    __tablename__ = "scraped_jobs"

    id = Column(Integer, primary_key=True, index=True)

    cache_key = Column(String(255), index=True, nullable=False)

    title = Column(String(180), nullable=False)
    company = Column(String(180), nullable=True)
    description = Column(Text, nullable=True)
    location = Column(String(120), nullable=True)
    required_skills = Column(JSON, default=list)

    url = Column(Text, nullable=True)
    source = Column(String(80), default="rekrute")
    category = Column(String(80), nullable=True)
    query = Column(String(255), nullable=True)

    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)