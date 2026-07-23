from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.vector_store import index_document, search_documents
from app.services.ai_extractor import call_ollama


router = APIRouter(prefix="/rag", tags=["RAG"])


class IndexDocumentRequest(BaseModel):
    text: str
    doc_type: str
    title: Optional[str] = None
    source_id: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    doc_type: Optional[str] = None


class AskRequest(BaseModel):
    question: str
    limit: int = 5


@router.post("/index")
def index_text(payload: IndexDocumentRequest):
    try:
        return index_document(
            text=payload.text,
            doc_type=payload.doc_type,
            metadata={
                "title": payload.title,
                "source_id": payload.source_id,
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/search")
def search(payload: SearchRequest):
    try:
        return {
            "results": search_documents(
                query=payload.query,
                limit=payload.limit,
                doc_type=payload.doc_type,
            )
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ask")
async def ask(payload: AskRequest):
    """
    Simple RAG endpoint:
    1. Search relevant docs from Qdrant
    2. Send retrieved context + question to LLM
    3. Return grounded answer
    """
    try:
        results = search_documents(
            query=payload.question,
            limit=payload.limit,
        )

        context_blocks = []

        for idx, result in enumerate(results, start=1):
            p = result["payload"]
            context_blocks.append(
                f"""
Context {idx}
Type: {p.get("type")}
Title: {p.get("title")}
Text:
{p.get("text")}
""".strip()
            )

        context = "\n\n---\n\n".join(context_blocks)

        prompt = f"""
You are SkillMatch AI, an assistant for a recruitment matching platform.

Answer the user's question using ONLY the retrieved context below.
If the answer is not in the context, say that the available context is insufficient.
Be clear, practical, and useful for candidates or recruiters.

Retrieved context:
{context}

User question:
{payload.question}
""".strip()

        answer = await call_ollama(prompt)

        return {
            "answer": answer,
            "retrieved_context": results,
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))