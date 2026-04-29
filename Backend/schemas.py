from pydantic import BaseModel
from typing import List, Optional, Dict

class CandidateCreate(BaseModel):
    full_name: str
    email: str
    experience_years: float = 0.0

class CandidateOut(BaseModel):
    id: int
    full_name: str
    email: str
    experience_years: float
    technical_skills: List[str] = []
    soft_skill_score: float = 0.0

class JobCreate(BaseModel):
    title: str
    required_skills: List[str]

class JobOut(BaseModel):
    id: int
    title: str
    required_skills: List[str]

class SoftSkillsSubmit(BaseModel):
    candidate_id: int
    answers: List[int]  # 1..5 each

class MatchRequest(BaseModel):
    candidate_id: int
    job_id: int

class MatchResponse(BaseModel):
    candidate_id: int
    job_id: int
    final_score_percent: float
    breakdown: Dict[str, float]
    matched_skills: List[str]
    missing_skills: List[str]
    learning_recommendations: Dict[str, str]
