# from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
# from sqlalchemy.orm import Session
# import pdfplumber
# import models
# from database import get_db

# router = APIRouter(prefix="/candidates", tags=["Candidates"])


# @router.post("/upload-cv")
# def upload_cv(
#     full_name: str,
#     email: str,
#     experience_years: float,
#     db: Session = Depends(get_db),
#     file: UploadFile = File(...)
# ):
#     if not file.filename.endswith(".pdf"):
#         raise HTTPException(status_code=400, detail="Only PDF files are allowed")

#     # -------- Extract text from PDF --------
#     cv_text = ""
#     with pdfplumber.open(file.file) as pdf:
#         for page in pdf.pages:
#             text = page.extract_text()
#             if text:
#                 cv_text += text + "\n"

#     if not cv_text.strip():
#         raise HTTPException(status_code=400, detail="Could not extract text from CV")

#     # -------- Create candidate --------
#     candidate = models.Candidate(
#         full_name=full_name,
#         email=email,
#         experience_years=experience_years,
#         cv_text=cv_text,
#         technical_skills="",   # optional, AI will infer from CV
#         soft_skill_score=0.0
#     )

#     db.add(candidate)
#     db.commit()
#     db.refresh(candidate)

#     return {
#         "message": "CV uploaded successfully",
#         "candidate_id": candidate.id
#     }

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
import pdfplumber
import models
from database import get_db

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.post("/upload-cv")
def upload_cv(
    full_name: str = Form(...),
    email: str = Form(...),
    experience_years: float = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # -------- Extract text from PDF --------
    cv_text = ""
    with pdfplumber.open(file.file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                cv_text += text + "\n"

    if not cv_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from CV")

    # -------- Create candidate --------
    candidate = models.Candidate(
        full_name=full_name,
        email=email,
        experience_years=experience_years,
        cv_text=cv_text,
        technical_skills="",
        soft_skill_score=0.0
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return {
        "message": "CV uploaded successfully",
        "candidate_id": candidate.id
    }
