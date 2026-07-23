import re
from html import unescape
from typing import Optional
from uuid import uuid5, NAMESPACE_URL

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..routes.auth import get_current_user, require_roles
from ..services.skill_extractor import extract_skills
from app.services.vector_store import index_document


router = APIRouter(prefix="/jobs", tags=["jobs"])

USER_AGENT = "SkillMatchAI-JobAnalyzer/1.0 (+student project; respectful single-page fetch)"


class JobImportRequest(BaseModel):
    url: Optional[HttpUrl] = None
    fallback_description: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    contract_type: Optional[str] = None
    save: bool = True


class JobAnalyzeRequest(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    description: str
    location: Optional[str] = None
    contract_type: Optional[str] = None


class JobImportResponse(BaseModel):
    job: schemas.JobOut
    extraction_method: str
    extraction_status: str
    detected_skills: list[str]
    compliance_note: str


class JobAnalysisResponse(BaseModel):
    title: str
    company: str
    description: str
    detected_skills: list[str]
    extraction_status: str


def _meta_content(html: str, names: list[str]) -> Optional[str]:
    for name in names:
        patterns = [
            rf'<meta[^>]+property=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
            rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{re.escape(name)}["\']',
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']{re.escape(name)}["\']',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, flags=re.I | re.S)
            if match:
                return unescape(match.group(1)).strip()

    return None


def _title_from_html(html: str) -> Optional[str]:
    title = _meta_content(html, ["og:title", "twitter:title"])

    if title:
        return title

    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)

    if match:
        return unescape(re.sub(r"\s+", " ", match.group(1))).strip()

    return None


def _clean_html_text(html: str) -> str:
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.I)
    html = re.sub(r"<noscript[\s\S]*?</noscript>", " ", html, flags=re.I)

    text = re.sub(r"<[^>]+>", " ", html)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()

    return text[:12000]


async def _fetch_public_page(url: str) -> tuple[Optional[str], Optional[str]]:
    try:
        async with httpx.AsyncClient(
            timeout=10,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            res = await client.get(url)

            if res.status_code >= 400:
                return None, f"The page returned HTTP {res.status_code}. Use manual description fallback."

            content_type = res.headers.get("content-type", "")

            if "text/html" not in content_type and "application/xhtml" not in content_type:
                return None, "The URL did not return an HTML page. Use manual description fallback."

            return res.text, None

    except Exception as exc:
        return None, f"Automatic extraction failed: {exc}. Use manual description fallback."


def _build_job_from_text(
    title: Optional[str],
    company: Optional[str],
    description: str,
    location: Optional[str],
    contract_type: Optional[str],
    created_by: Optional[int],
) -> models.Job:
    skills = extract_skills(description)

    safe_title = (title or "Imported External Job Offer").strip()[:160]
    safe_company = (company or "External platform").strip()[:160]

    return models.Job(
        title=safe_title,
        company=safe_company,
        description=description.strip(),
        required_skills=skills,
        location=location,
        contract_type=contract_type or "External offer",
        created_by=created_by,
    )


def _index_job_in_qdrant(job: models.Job) -> None:
    """
    Indexes a job offer in Qdrant for semantic search and RAG.
    This should not block job creation if Qdrant fails.
    """
    job_text = f"""
Job title: {job.title}
Company: {job.company}
Location: {job.location or "Not specified"}
Contract type: {job.contract_type or "Not specified"}
Required skills: {", ".join(job.required_skills or [])}

Description:
{job.description}
""".strip()

    stable_point_id = str(uuid5(NAMESPACE_URL, f"skillmatch-job-{job.id}"))

    try:
        index_document(
            text=job_text,
            doc_type="job",
            metadata={
                "source_id": str(job.id),
                "job_id": job.id,
                "title": job.title,
                "company": job.company,
                "skills": job.required_skills or [],
            },
            point_id=stable_point_id,
        )
    except Exception as exc:
        print(f"[QDRANT] Failed to index job {job.id}: {exc}")


@router.post("", response_model=schemas.JobOut)
def create_job(
    payload: schemas.JobCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("recruiter", "admin")),
):
    data = payload.model_dump()

    if not data.get("required_skills"):
        data["required_skills"] = extract_skills(data["description"])

    job = models.Job(**data, created_by=current_user.id)

    db.add(job)
    db.commit()
    db.refresh(job)

    _index_job_in_qdrant(job)

    return job


@router.post("/analyze-description", response_model=JobAnalysisResponse)
def analyze_job_description(
    payload: JobAnalyzeRequest,
    current_user: models.User = Depends(get_current_user),
):
    description = payload.description.strip()

    if len(description) < 40:
        raise HTTPException(
            status_code=400,
            detail="Paste a longer job description so the AI engine can extract meaningful skills.",
        )

    detected = extract_skills(description)

    return JobAnalysisResponse(
        title=(payload.title or "Manual Job Analysis").strip(),
        company=(payload.company or "External company").strip(),
        description=description,
        detected_skills=detected,
        extraction_status="manual_description_analyzed",
    )


@router.post("/import-from-url", response_model=JobImportResponse)
async def import_from_url(
    payload: JobImportRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    extraction_method = "manual-fallback"
    extraction_status = "used_manual_description"

    description = (payload.fallback_description or "").strip()
    title = payload.title
    company = payload.company

    if payload.url:
        html, fetch_error = await _fetch_public_page(str(payload.url))

        if html:
            extracted_title = _title_from_html(html)
            meta_description = _meta_content(
                html,
                ["description", "og:description", "twitter:description"],
            )
            page_text = _clean_html_text(html)
            candidate_description = meta_description or page_text

            if candidate_description and len(candidate_description) > len(description):
                description = candidate_description
                extraction_method = "public-url"
                extraction_status = "extracted_from_public_page"

            if extracted_title and not title:
                title = extracted_title

        elif not description:
            raise HTTPException(
                status_code=400,
                detail=fetch_error or "Could not extract the URL. Paste the job description manually.",
            )

        else:
            extraction_status = "url_blocked_used_manual_fallback"

    if not description or len(description) < 40:
        raise HTTPException(
            status_code=400,
            detail="Provide a job URL that is publicly readable or paste the job description manually.",
        )

    created_by = current_user.id if current_user.role in ("recruiter", "admin") else None

    job = _build_job_from_text(
        title=title,
        company=company,
        description=description,
        location=payload.location,
        contract_type=payload.contract_type,
        created_by=created_by,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    _index_job_in_qdrant(job)

    return JobImportResponse(
        job=job,
        extraction_method=extraction_method,
        extraction_status=extraction_status,
        detected_skills=job.required_skills or [],
        compliance_note=(
            "SkillMatch performs only a single public-page extraction when accessible. "
            "If a platform blocks extraction or requires authentication, the user must paste "
            "the job description manually. The system does not scrape candidate profiles."
        ),
    )


@router.get("", response_model=list[schemas.JobOut])
def list_jobs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.Job).order_by(models.Job.id.desc()).all()


@router.get("/{job_id}", response_model=schemas.JobOut)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = db.get(models.Job, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.delete("/{job_id}")
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("recruiter", "admin")),
):
    job = db.get(models.Job, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if current_user.role == "recruiter" and job.created_by not in (None, current_user.id):
        raise HTTPException(status_code=403, detail="You can only delete your own offers")

    db.delete(job)
    db.commit()

    return {"ok": True}