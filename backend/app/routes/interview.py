from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.routes.auth import get_current_user, require_roles
from app.agents.interview_agent import (
    generate_interview_questions,
    evaluate_interview_answer,
)


router = APIRouter(prefix="/interview", tags=["Interview Agent"])


class InterviewGenerateRequest(BaseModel):
    candidate_id: int
    job_id: int
    matched_skills: List[str] = []
    missing_skills: List[str] = []


class InterviewGenerateMeRequest(BaseModel):
    job_id: int
    matched_skills: List[str] = []
    missing_skills: List[str] = []


class InterviewEvaluateRequest(BaseModel):
    candidate_id: int
    job_id: int
    question: str
    answer: str


class InterviewEvaluateMeRequest(BaseModel):
    job_id: int
    question: str
    answer: str


def _get_candidate_or_404(db: Session, candidate_id: int) -> models.Candidate:
    candidate = db.get(models.Candidate, candidate_id)

    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return candidate


def _get_job_or_404(db: Session, job_id: int) -> models.Job:
    job = db.get(models.Job, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


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


def _check_candidate_access(candidate: models.Candidate, current_user: models.User) -> None:
    if current_user.role == "candidate" and candidate.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only access your own interview preparation.",
        )


async def _generate_for_candidate_and_job(
    candidate: models.Candidate,
    job: models.Job,
    matched_skills: List[str],
    missing_skills: List[str],
):
    return await generate_interview_questions(
        job_title=job.title,
        job_description=job.description,
        candidate_name=candidate.full_name,
        candidate_skills=candidate.skills or [],
        matched_skills=matched_skills,
        missing_skills=missing_skills,
    )


async def _evaluate_for_candidate_and_job(
    candidate: models.Candidate,
    job: models.Job,
    question: str,
    answer: str,
):
    if len(answer.strip()) < 5:
        raise HTTPException(status_code=400, detail="Answer is too short to evaluate.")

    return await evaluate_interview_answer(
        question=question,
        answer=answer,
        job_title=job.title,
        job_description=job.description,
        candidate_skills=candidate.skills or [],
    )


@router.post("/generate")
async def generate(
    payload: InterviewGenerateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Generic endpoint for recruiters/admins or advanced testing.
    Uses explicit candidate_id and job_id.
    """
    candidate = _get_candidate_or_404(db, payload.candidate_id)
    job = _get_job_or_404(db, payload.job_id)

    _check_candidate_access(candidate, current_user)

    return await _generate_for_candidate_and_job(
        candidate=candidate,
        job=job,
        matched_skills=payload.matched_skills,
        missing_skills=payload.missing_skills,
    )


@router.post("/generate/me")
async def generate_for_me(
    payload: InterviewGenerateMeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("candidate", "admin")),
):
    """
    Candidate-friendly endpoint.
    The frontend only sends job_id.
    The backend automatically finds the logged-in candidate profile.
    """
    candidate = _get_my_candidate_profile(db, current_user)
    job = _get_job_or_404(db, payload.job_id)

    return await _generate_for_candidate_and_job(
        candidate=candidate,
        job=job,
        matched_skills=payload.matched_skills,
        missing_skills=payload.missing_skills,
    )


@router.post("/evaluate")
async def evaluate(
    payload: InterviewEvaluateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Generic endpoint for recruiters/admins or advanced testing.
    Uses explicit candidate_id and job_id.
    """
    candidate = _get_candidate_or_404(db, payload.candidate_id)
    job = _get_job_or_404(db, payload.job_id)

    _check_candidate_access(candidate, current_user)

    return await _evaluate_for_candidate_and_job(
        candidate=candidate,
        job=job,
        question=payload.question,
        answer=payload.answer,
    )


@router.post("/evaluate/me")
async def evaluate_for_me(
    payload: InterviewEvaluateMeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("candidate", "admin")),
):
    """
    Candidate-friendly endpoint.
    The frontend only sends job_id, question, and answer.
    """
    candidate = _get_my_candidate_profile(db, current_user)
    job = _get_job_or_404(db, payload.job_id)

    return await _evaluate_for_candidate_and_job(
        candidate=candidate,
        job=job,
        question=payload.question,
        answer=payload.answer,
    )