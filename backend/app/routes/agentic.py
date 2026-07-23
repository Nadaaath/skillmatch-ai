from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.routes.auth import get_current_user, require_roles
from app.agents.orchestrator import run_full_candidate_job_analysis
from app.agents.langgraph_orchestrator import run_langgraph_candidate_job_analysis

router = APIRouter(prefix="/agentic", tags=["Agentic AI Orchestrator"])


class RunForMeRequest(BaseModel):
    job_id: int


class RunExplicitRequest(BaseModel):
    candidate_id: int
    job_id: int


def _get_job_or_404(db: Session, job_id: int) -> models.Job:
    job = db.get(models.Job, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


def _get_candidate_or_404(db: Session, candidate_id: int) -> models.Candidate:
    candidate = db.get(models.Candidate, candidate_id)

    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return candidate


def _get_my_candidate_profile(db: Session, current_user: models.User) -> models.Candidate:
    candidate = (
        db.query(models.Candidate)
        .filter(models.Candidate.user_id == current_user.id)
        .order_by(models.Candidate.id.desc())
        .first()
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="No candidate profile found for this account. Upload a CV first.",
        )

    return candidate


@router.post("/run/me")
async def run_for_me(
    payload: RunForMeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("candidate", "admin")),
):
    candidate = _get_my_candidate_profile(db, current_user)
    job = _get_job_or_404(db, payload.job_id)

    return await run_full_candidate_job_analysis(candidate, job)


@router.post("/run")
async def run_explicit(
    payload: RunExplicitRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    candidate = _get_candidate_or_404(db, payload.candidate_id)
    job = _get_job_or_404(db, payload.job_id)

    if current_user.role == "candidate" and candidate.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only run analysis for your own profile.",
        )

    return await run_full_candidate_job_analysis(candidate, job)

@router.post("/run-langgraph/me")
async def run_langgraph_for_me(
    payload: RunForMeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("candidate", "admin")),
):
    candidate = _get_my_candidate_profile(db, current_user)
    job = _get_job_or_404(db, payload.job_id)

    return await run_langgraph_candidate_job_analysis(candidate, job)


@router.post("/run-langgraph")
async def run_langgraph_explicit(
    payload: RunExplicitRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    candidate = _get_candidate_or_404(db, payload.candidate_id)
    job = _get_job_or_404(db, payload.job_id)

    if current_user.role == "candidate" and candidate.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only run analysis for your own profile.",
        )

    return await run_langgraph_candidate_job_analysis(candidate, job)