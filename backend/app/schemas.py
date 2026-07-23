from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    class Config:
        from_attributes = True

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "candidate"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class CandidateCreate(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    education: Optional[str] = None
    experience: Optional[str] = None
    skills: List[str] = []

class CandidateOut(CandidateCreate):
    id: int
    user_id: Optional[int] = None
    cv_text: Optional[str] = None
    class Config:
        from_attributes = True

class JobCreate(BaseModel):
    title: str
    company: str
    description: str
    required_skills: List[str] = []
    location: Optional[str] = None
    contract_type: Optional[str] = None

class JobOut(JobCreate):
    id: int
    created_by: Optional[int] = None
    class Config:
        from_attributes = True

class MatchOut(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    score: float
    skill_score: float
    semantic_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    explanation: Optional[str] = None
    class Config:
        from_attributes = True

class AgentRequest(BaseModel):
    message: str
    candidate_id: Optional[int] = None
    job_id: Optional[int] = None
    mode: str = "candidate"

class AgentResponse(BaseModel):
    response: str
    context: dict[str, Any]
