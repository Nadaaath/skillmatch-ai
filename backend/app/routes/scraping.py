from typing import Optional
from uuid import uuid5, NAMESPACE_URL

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app import models
from app.routes.auth import require_roles, get_current_user
from app.agents.scraping_agent import CATEGORIES, scrape_rekrute_jobs
from app.services.vector_store import index_document


router = APIRouter(prefix="/scraping", tags=["Scraping Agent"])
CACHE_TTL_HOURS = 24

class RekruteScrapeRequest(BaseModel):
    category: str = "it"
    query: Optional[str] = None
    limit: int = 10
    save: bool = True


def _index_job_in_qdrant(job: models.Job) -> None:
    job_text = f"""
Job title: {job.title}
Company: {job.company}
Location: {job.location or "Not specified"}
Contract type: {job.contract_type or "Scraped job"}
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
                "source": "rekrute",
            },
            point_id=stable_point_id,
        )
    except Exception as exc:
        print(f"[QDRANT] Failed to index scraped job {job.id}: {exc}")

def _make_cache_key(category: str, query: str | None) -> str:
    return f"rekrute:{category}:{(query or '').strip().lower()}"


def _load_scraped_jobs_from_cache(
    db: Session,
    cache_key: str,
) -> list[dict] | None:
    expiry = datetime.now(timezone.utc) - timedelta(hours=CACHE_TTL_HOURS)

    rows = (
        db.query(models.ScrapedJob)
        .filter(
            models.ScrapedJob.cache_key == cache_key,
            models.ScrapedJob.scraped_at >= expiry,
        )
        .order_by(models.ScrapedJob.id.desc())
        .all()
    )

    if not rows:
        return None

    return [
        {
            "title": row.title,
            "company": row.company,
            "description": row.description,
            "location": row.location,
            "required_skills": row.required_skills or [],
            "url": row.url,
            "source": row.source,
            "category": row.category,
        }
        for row in rows
    ]


def _save_scraped_jobs_to_cache(
    db: Session,
    cache_key: str,
    jobs: list[dict],
    category: str,
    query: str | None,
) -> None:
    db.query(models.ScrapedJob).filter(
        models.ScrapedJob.cache_key == cache_key
    ).delete()

    for item in jobs:
        db.add(
            models.ScrapedJob(
                cache_key=cache_key,
                title=item.get("title") or "Untitled job",
                company=item.get("company") or "Rekrute",
                description=item.get("description") or "",
                location=item.get("location") or "Morocco",
                required_skills=item.get("required_skills") or [],
                url=item.get("url"),
                source=item.get("source") or "rekrute",
                category=category,
                query=query,
                scraped_at=datetime.now(timezone.utc),
            )
        )

    db.commit()

@router.get("/categories")
def categories():
    return CATEGORIES


@router.post("/rekrute")
def scrape_rekrute(
    payload: RekruteScrapeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("candidate", "recruiter", "admin")),
):
    """
    Scrapes public Rekrute jobs and optionally saves them into PostgreSQL.

    Cache behavior:
    - same category/query returns cached scraped jobs for 24 hours
    - avoids repeated calls to Rekrute
    - if Rekrute blocks, returns clean fallback response
    """
    if payload.category not in CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Choose one of: {list(CATEGORIES.keys())}",
        )

    limit = min(max(payload.limit, 1), 20)
    cache_key = _make_cache_key(payload.category, payload.query)

    cached_jobs = _load_scraped_jobs_from_cache(db, cache_key)

    if cached_jobs is not None:
        jobs_to_return = cached_jobs[:limit]

        return {
            "scrape": {
                "source": "rekrute",
                "category": payload.category,
                "query": payload.query,
                "status": "cache_hit",
                "count": len(jobs_to_return),
                "cache_key": cache_key,
                "cache_ttl_hours": CACHE_TTL_HOURS,
            },
            "jobs": jobs_to_return,
            "saved_jobs_count": 0,
            "saved_jobs": [],
            "compliance_note": (
                "Results were returned from the PostgreSQL scraping cache. "
                "No new request was sent to Rekrute."
            ),
        }

    result = scrape_rekrute_jobs(
        category=payload.category,
        query=payload.query,
        limit=limit,
    )

    if result["status"] != "success":
        return {
            "scrape": {
                "source": result.get("source"),
                "url": result.get("url"),
                "category": payload.category,
                "query": payload.query,
                "status": result.get("status"),
                "error": result.get("error"),
                "cache_key": cache_key,
            },
            "jobs": [],
            "saved_jobs_count": 0,
            "saved_jobs": [],
            "compliance_note": (
                "Rekrute blocked or rejected the automatic public-page request. "
                "SkillMatch does not bypass anti-bot restrictions. "
                "The user can paste the job description manually or use already saved/imported jobs."
            ),
        }

    _save_scraped_jobs_to_cache(
        db=db,
        cache_key=cache_key,
        jobs=result["jobs"],
        category=payload.category,
        query=payload.query,
    )

    saved_jobs = []

    if payload.save:
        for item in result["jobs"]:
            existing = None

            if item.get("url"):
                existing = (
                    db.query(models.Job)
                    .filter(models.Job.description.contains(item["url"]))
                    .first()
                )

            if existing:
                continue

            description = item["description"] or ""

            if item.get("url"):
                description = f"{description}\n\nSource URL: {item['url']}"

            job = models.Job(
                title=item["title"],
                company=item["company"],
                description=description,
                required_skills=item["required_skills"],
                location=item["location"],
                contract_type="Scraped from Rekrute",
                created_by=current_user.id,
            )

            db.add(job)
            db.commit()
            db.refresh(job)

            _index_job_in_qdrant(job)

            saved_jobs.append(
                {
                    "id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "skills": job.required_skills or [],
                }
            )

    return {
        "scrape": {
            "source": result["source"],
            "url": result["url"],
            "category": result["category"],
            "query": result["query"],
            "status": "fresh_scrape",
            "count": result["count"],
            "cache_key": cache_key,
            "cache_ttl_hours": CACHE_TTL_HOURS,
        },
        "jobs": result["jobs"],
        "saved_jobs_count": len(saved_jobs),
        "saved_jobs": saved_jobs,
        "compliance_note": (
            "This endpoint fetches public Rekrute job listings only, with a limited request volume. "
            "Results are cached in PostgreSQL for 24 hours. "
            "It does not scrape candidate profiles or authenticated pages."
        ),
    }