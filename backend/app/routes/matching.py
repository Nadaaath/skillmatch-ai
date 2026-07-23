from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
from ..routes.auth import get_current_user, require_roles
from ..services.matching_engine import calculate_match

router = APIRouter(prefix="/matching", tags=["matching"])

def assert_candidate_access(candidate: models.Candidate, user: models.User):
    if user.role == "candidate" and candidate.user_id != user.id:
        raise HTTPException(status_code=403, detail="You can only compute matches for your own profile")

@router.post("/candidate/{candidate_id}/job/{job_id}", response_model=schemas.MatchOut)
def compute_match(candidate_id: int, job_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    candidate = db.get(models.Candidate, candidate_id)
    job = db.get(models.Job, job_id)
    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Candidate or job not found")
    assert_candidate_access(candidate, current_user)

    result = calculate_match(candidate.cv_text or candidate.experience or "", candidate.skills or [], job.description, job.required_skills or [])
    existing = db.query(models.Match).filter_by(candidate_id=candidate_id, job_id=job_id).first()
    if existing:
        for k, v in result.items():
            setattr(existing, k, v)
        match = existing
    else:
        match = models.Match(candidate_id=candidate_id, job_id=job_id, **result)
        db.add(match)
    db.commit()
    db.refresh(match)
    return match

@router.get("/candidate/{candidate_id}", response_model=list[schemas.MatchOut])
def candidate_matches(candidate_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    candidate = db.get(models.Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    assert_candidate_access(candidate, current_user)
    return db.query(models.Match).filter_by(candidate_id=candidate_id).order_by(models.Match.score.desc()).all()

@router.get("/job/{job_id}/ranking", response_model=list[schemas.MatchOut])
def job_ranking(job_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_roles("recruiter", "admin"))):
    return db.query(models.Match).filter_by(job_id=job_id).order_by(models.Match.score.desc()).all()

@router.post("/candidate/{candidate_id}/all-jobs", response_model=list[schemas.MatchOut])
def compute_all_matches(candidate_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    candidate = db.get(models.Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    assert_candidate_access(candidate, current_user)
    jobs = db.query(models.Job).all()
    for job in jobs:
        result = calculate_match(candidate.cv_text or candidate.experience or "", candidate.skills or [], job.description, job.required_skills or [])
        existing = db.query(models.Match).filter_by(candidate_id=candidate_id, job_id=job.id).first()
        if existing:
            for k, v in result.items():
                setattr(existing, k, v)
        else:
            db.add(models.Match(candidate_id=candidate_id, job_id=job.id, **result))
    db.commit()
    return db.query(models.Match).filter_by(candidate_id=candidate_id).order_by(models.Match.score.desc()).all()
