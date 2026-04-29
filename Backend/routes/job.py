from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
import models

from ai_engine import (
    compute_skill_match_ratio,
    compute_tfidf_similarity,
)

from ai_engine_bert import compute_bert_similarity
from utils.recommendations import get_recommendations

router = APIRouter(prefix="/jobs", tags=["Jobs"])


# -------------------------------------------------
# ✅ CREATE JOB
# -------------------------------------------------
@router.post("/create")
def create_job(
    title: str,
    required_skills: str,
    db: Session = Depends(get_db)
):
    """
    Create a new job posting.
    required_skills: comma-separated string
    """
    job = models.Job(
        title=title,
        required_skills=required_skills.lower()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "message": "Job created successfully",
        "job_id": job.id,
        "title": job.title,
        "required_skills": job.required_skills
    }


# -------------------------------------------------
# ✅ MATCH CANDIDATE ↔ JOB
# -------------------------------------------------
@router.get("/match")
def match_job(
    candidate_id: int,
    job_id: int,
    db: Session = Depends(get_db)
):
    candidate = db.query(models.Candidate).filter(
        models.Candidate.id == candidate_id
    ).first()

    job = db.query(models.Job).filter(
        models.Job.id == job_id
    ).first()

    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Candidate or Job not found")

    # -------------------------
    # Rule-based skill matching
    # -------------------------
    skills_source = (
    candidate.technical_skills
    if candidate.technical_skills.strip()
    else candidate.cv_text
)
    skill_match_ratio, missing_skills = compute_skill_match_ratio(
        skills_source,
         job.required_skills
    )

    # -------------------------
    # TF-IDF similarity
    # -------------------------
    tfidf_similarity = compute_tfidf_similarity(
        candidate.cv_text or candidate.technical_skills,
        job.required_skills
    )

    # -------------------------
    # BERT similarity
    # -------------------------
    bert_similarity = compute_bert_similarity(
        candidate.cv_text or candidate.technical_skills,
        job.required_skills
    )

    # -------------------------
    # Final explainable score
    # -------------------------
    hiring_probability = round(
        0.3 * skill_match_ratio +
        0.3 * tfidf_similarity +
        0.4 * bert_similarity,
        3
    )

    return {
        "candidate_id": candidate.id,
        "job_id": job.id,
        "skill_match_ratio": round(skill_match_ratio, 3),
        "tfidf_similarity": round(tfidf_similarity, 3),
        "bert_similarity": round(bert_similarity, 3),
        "hiring_probability": hiring_probability,
        "missing_skills": missing_skills,
        "recommendations": get_recommendations(missing_skills,hiring_probability)
    }
