import json
import re
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.llm_service import generate_text


router = APIRouter(prefix="/ai", tags=["AI Extraction"])


class JobExtractionRequest(BaseModel):
    text: str


def _extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found in LLM response.")

    return json.loads(match.group(0))


def _safe_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        return [x.strip() for x in value.split(",") if x.strip()]
    return []


def _normalize_result(data: Dict[str, Any]) -> Dict[str, Any]:
    technical_skills = _safe_list(data.get("technical_skills"))
    tools = _safe_list(data.get("tools"))
    databases = _safe_list(data.get("databases"))
    methodologies = _safe_list(data.get("methodologies"))
    soft_skills = _safe_list(data.get("soft_skills"))

    unified = []

    for group in [technical_skills, tools, databases, methodologies]:
        for item in group:
            if item.lower() not in [x.lower() for x in unified]:
                unified.append(item)

    return {
        "title": data.get("title"),
        "company": data.get("company"),
        "location": data.get("location"),
        "contract_type": data.get("contract_type"),
        "language": data.get("language"),
        "summary": data.get("summary"),
        "technical_skills": technical_skills,
        "tools": tools,
        "databases": databases,
        "methodologies": methodologies,
        "soft_skills": soft_skills,
        "responsibilities": _safe_list(data.get("responsibilities")),
        "experience_required": data.get("experience_required"),
        "education_required": data.get("education_required"),
        "missing_or_unclear_information": _safe_list(data.get("missing_or_unclear_information")),
        "english_translation": data.get("english_translation"),
        "unified_skills": unified,
    }


@router.post("/extract-job")
async def extract_job(payload: JobExtractionRequest):
    text = payload.text.strip()

    if len(text) < 40:
        raise HTTPException(
            status_code=400,
            detail="Paste a longer job description.",
        )

    prompt = f"""
You are an expert HR and technical recruitment assistant.

Extract structured information from this job offer.

Return ONLY valid JSON. No markdown. No explanation.

JSON schema:
{{
  "title": string or null,
  "company": string or null,
  "location": string or null,
  "contract_type": string or null,
  "language": string,
  "summary": string,
  "technical_skills": [string],
  "tools": [string],
  "databases": [string],
  "methodologies": [string],
  "soft_skills": [string],
  "responsibilities": [string],
  "experience_required": string or null,
  "education_required": string or null,
  "missing_or_unclear_information": [string],
  "english_translation": string
}}

Rules:
- Detect the real job title. Do not use hashtags as title.
- If company, location, or contract type are present, extract them.
- Extract concrete technical skills such as Python, Django, Docker, SQL, Power BI, ETL, Spark, etc.
- Extract tools separately, such as Git, Jira, Trello, Power BI, Excel.
- Extract databases separately.
- Extract methodologies separately, such as Agile, Scrum, DevOps, CI/CD.
- Extract soft skills separately.
- If the offer is in French, keep fields in English-compatible structured format but preserve proper names.
- The english_translation should summarize the full offer in English.

Job offer:
{text}
""".strip()

    try:
        raw = await generate_text(prompt)
        data = _extract_json(raw)
        return _normalize_result(data)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))