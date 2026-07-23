from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.llm_service import generate_text


router = APIRouter(prefix="/llm", tags=["LLM Provider"])


class LLMTestRequest(BaseModel):
    prompt: str


@router.get("/status")
def llm_status():
    import os

    return {
        "provider": os.getenv("LLM_PROVIDER", "ollama"),
        "ollama_model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite"),
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
    }


@router.post("/test")
async def test_llm(payload: LLMTestRequest):
    try:
        answer = await generate_text(payload.prompt)

        return {
            "answer": answer,
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))