from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
from ..services.agent_service import generate_agent_response
from ..routes.auth import get_current_user

router = APIRouter(prefix="/agent", tags=["agent"])

def build_context(db: Session, candidate_id: int | None, job_id: int | None, current_user: models.User) -> dict:
    context = {}
    if candidate_id:
        c = db.get(models.Candidate, candidate_id)
        if not c:
            raise HTTPException(status_code=404, detail="Candidate not found")
        if current_user.role == "candidate" and c.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only use your own candidate profile as agent context")
        context["candidate"] = {
            "id": c.id,
            "name": c.full_name,
            "skills": c.skills,
            "cv_excerpt": (c.cv_text or "")[:1500],
        }
    if job_id:
        j = db.get(models.Job, job_id)
        if not j:
            raise HTTPException(status_code=404, detail="Job not found")
        context["job"] = {
            "id": j.id,
            "title": j.title,
            "company": j.company,
            "required_skills": j.required_skills,
            "description": j.description[:1500],
        }
    if candidate_id and job_id:
        m = db.query(models.Match).filter_by(candidate_id=candidate_id, job_id=job_id).first()
        if m:
            context["match"] = {
                "score": m.score,
                "skill_score": m.skill_score,
                "semantic_score": m.semantic_score,
                "matched_skills": m.matched_skills,
                "missing_skills": m.missing_skills,
                "explanation": m.explanation,
            }
    return context

@router.post("/chat", response_model=schemas.AgentResponse)
async def chat(payload: schemas.AgentRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    context = build_context(db, payload.candidate_id, payload.job_id, current_user)
    response = await generate_agent_response(payload.message, context)
    conv = models.AgentConversation(
        user_role=payload.mode,
        message=payload.message,
        response=response,
        context_type="chat",
    )
    db.add(conv)
    db.commit()
    return {"response": response, "context": context}

@router.post("/explain-match", response_model=schemas.AgentResponse)
async def explain_match(payload: schemas.AgentRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    message = payload.message or "Explain this candidate-job match and give improvement advice."
    context = build_context(db, payload.candidate_id, payload.job_id, current_user)
    response = await generate_agent_response(message, context)
    return {"response": response, "context": context}

@router.post("/interview-questions", response_model=schemas.AgentResponse)
async def interview_questions(payload: schemas.AgentRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    context = build_context(db, payload.candidate_id, payload.job_id, current_user)
    response = await generate_agent_response("Generate personalized interview questions for this job and candidate.", context)
    return {"response": response, "context": context}

@router.post("/cv-feedback", response_model=schemas.AgentResponse)
async def cv_feedback(payload: schemas.AgentRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    context = build_context(db, payload.candidate_id, payload.job_id, current_user)
    response = await generate_agent_response("Give concrete CV improvement suggestions for this candidate.", context)
    return {"response": response, "context": context}
