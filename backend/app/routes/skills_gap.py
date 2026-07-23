from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.skills_gap_agent import analyze_skills_gap


router = APIRouter(prefix="/skills-gap", tags=["Skills Gap Agent"])


class SkillsGapRequest(BaseModel):
    candidate_skills: List[str]
    job_skills: List[str]
    job_text: str


@router.post("/analyze")
def analyze(payload: SkillsGapRequest):
    try:
        return analyze_skills_gap(
            candidate_skills=payload.candidate_skills,
            job_skills=payload.job_skills,
            job_text=payload.job_text,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))