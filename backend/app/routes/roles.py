from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.role_knowledge_service import (
    index_roles_dataset,
    load_role_dataset,
    search_roles,
    recommend_from_roles,
)


router = APIRouter(prefix="/roles", tags=["Role Knowledge Base"])


class RoleSearchRequest(BaseModel):
    query: str
    limit: int = 5


class RoleRecommendRequest(BaseModel):
    job_text: str
    candidate_skills: List[str] = []
    limit: int = 5


@router.get("/status")
def roles_status():
    try:
        roles = load_role_dataset()
        return {
            "dataset_loaded": True,
            "roles_count": len(roles),
        }
    except Exception as exc:
        return {
            "dataset_loaded": False,
            "error": str(exc),
        }


@router.post("/index-dataset")
def index_dataset():
    try:
        return index_roles_dataset()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/search")
def search(payload: RoleSearchRequest):
    try:
        return {
            "results": search_roles(
                query=payload.query,
                limit=payload.limit,
            )
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/recommend")
def recommend(payload: RoleRecommendRequest):
    try:
        return recommend_from_roles(
            job_text=payload.job_text,
            candidate_skills=payload.candidate_skills,
            limit=payload.limit,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))