from uuid import uuid5, NAMESPACE_URL

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..routes.auth import get_current_user, require_roles
from ..services.cv_parser import UPLOAD_DIR, save_upload_file, extract_text_from_pdf
from ..services.skill_extractor import extract_skills
from app.services.vector_store import index_document


router = APIRouter(prefix="/candidates", tags=["candidates"])


def _index_candidate_in_qdrant(candidate: models.Candidate) -> None:
    """
    Indexes a candidate profile in Qdrant for semantic search and RAG.
    This should not block candidate creation/upload if Qdrant fails.
    """
    candidate_text = f"""
Candidate name: {candidate.full_name}
Email: {candidate.email or "Not specified"}
Skills: {", ".join(candidate.skills or [])}

CV text:
{candidate.cv_text or ""}
""".strip()

    stable_point_id = str(uuid5(NAMESPACE_URL, f"skillmatch-candidate-{candidate.id}"))

    try:
        index_document(
            text=candidate_text,
            doc_type="candidate",
            metadata={
                "source_id": str(candidate.id),
                "candidate_id": candidate.id,
                "name": candidate.full_name,
                "email": candidate.email,
                "skills": candidate.skills or [],
            },
            point_id=stable_point_id,
        )
    except Exception as exc:
        print(f"[QDRANT] Failed to index candidate {candidate.id}: {exc}")


@router.post("", response_model=schemas.CandidateOut)
def create_candidate(
    payload: schemas.CandidateCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("candidate", "admin")),
):
    candidate = models.Candidate(
        **payload.model_dump(),
        user_id=current_user.id if current_user.role == "candidate" else None,
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    _index_candidate_in_qdrant(candidate)

    return candidate


@router.get("", response_model=list[schemas.CandidateOut])
def list_candidates(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("recruiter", "admin")),
):
    return db.query(models.Candidate).order_by(models.Candidate.id.desc()).all()


@router.get("/me", response_model=schemas.CandidateOut | None)
def my_candidate_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("candidate", "admin")),
):
    return (
        db.query(models.Candidate)
        .filter(models.Candidate.user_id == current_user.id)
        .order_by(models.Candidate.id.desc())
        .first()
    )


@router.get("/{candidate_id}", response_model=schemas.CandidateOut)
def get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    candidate = db.get(models.Candidate, candidate_id)

    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    if current_user.role == "candidate" and candidate.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only access your own candidate profile",
        )

    return candidate


@router.post("/upload-cv", response_model=schemas.CandidateOut)
def upload_cv(
    full_name: str = Form(...),
    email: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("candidate", "admin")),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    path = UPLOAD_DIR / f"{full_name.replace(' ', '_')}_{file.filename}"

    save_upload_file(file, path)

    cv_text = extract_text_from_pdf(path)
    skills = extract_skills(cv_text)

    candidate = (
        db.query(models.Candidate)
        .filter(models.Candidate.user_id == current_user.id)
        .first()
    )

    if candidate:
        candidate.full_name = full_name
        candidate.email = email
        candidate.cv_text = cv_text
        candidate.skills = skills
    else:
        candidate = models.Candidate(
            full_name=full_name,
            email=email,
            cv_text=cv_text,
            skills=skills,
            user_id=current_user.id,
        )
        db.add(candidate)

    db.commit()
    db.refresh(candidate)

    _index_candidate_in_qdrant(candidate)

    return candidate