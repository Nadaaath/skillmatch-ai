from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..routes.auth import require_roles

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary")
def summary(db: Session = Depends(get_db), current_user: models.User = Depends(require_roles("recruiter", "admin"))):
    candidates = db.query(models.Candidate).all()
    jobs = db.query(models.Job).all()
    matches = db.query(models.Match).all()

    demanded = Counter()
    missing = Counter()
    for job in jobs:
        demanded.update(job.required_skills or [])
    for match in matches:
        missing.update(match.missing_skills or [])

    avg_score = round(sum(m.score for m in matches) / len(matches), 2) if matches else 0

    return {
        "total_candidates": len(candidates),
        "total_jobs": len(jobs),
        "total_matches": len(matches),
        "average_match_score": avg_score,
        "most_demanded_skills": demanded.most_common(10),
        "most_missing_skills": missing.most_common(10),
    }
