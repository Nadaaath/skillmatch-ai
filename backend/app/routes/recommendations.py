from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..routes.auth import get_current_user
from ..services.skill_extractor import categorize_skills, build_learning_plan

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

def assert_candidate_access(candidate: models.Candidate, user: models.User):
    if user.role == "candidate" and candidate.user_id != user.id:
        raise HTTPException(status_code=403, detail="You can only access your own recommendations")

@router.get("/candidate/{candidate_id}/profile")
def candidate_profile_insights(candidate_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    candidate = db.get(models.Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    assert_candidate_access(candidate, current_user)
    skills = candidate.skills or []
    categories = categorize_skills(skills)
    strengths = sorted(categories.keys())
    return {
        "candidate_id": candidate.id,
        "total_skills": len(skills),
        "skill_categories": categories,
        "strength_areas": strengths,
        "profile_quality": min(100, 30 + len(skills) * 4),
        "advice": "Add quantified project results and align your CV keywords with the target offer."
    }

@router.get("/candidate/{candidate_id}/job/{job_id}")
def job_recommendations(candidate_id: int, job_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    candidate = db.get(models.Candidate, candidate_id)
    job = db.get(models.Job, job_id)
    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Candidate or job not found")
    assert_candidate_access(candidate, current_user)
    match = db.query(models.Match).filter_by(candidate_id=candidate_id, job_id=job_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Compute the match first")
    missing = match.missing_skills or []
    matched = match.matched_skills or []
    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "score": match.score,
        "matched_skills": matched,
        "missing_skills": missing,
        "learning_plan": build_learning_plan(missing),
        "portfolio_project": build_project_idea(job.title, missing),
        "cv_keywords_to_add": missing[:6],
        "next_best_action": "Build one small project proving the top 2 missing skills, then update your CV and recompute the match."
    }

def build_project_idea(job_title: str, missing_skills: list[str]) -> dict:
    top = missing_skills[:3] or ["project documentation", "testing", "clean architecture"]
    return {
        "title": f"Mini-project to improve match for {job_title}",
        "description": f"Create a small end-to-end project demonstrating {', '.join(top)}.",
        "deliverables": [
            "GitHub repository with clean README",
            "Screenshots of the running app",
            "Short architecture diagram",
            "Explanation of how the project uses the missing skills"
        ]
    }
