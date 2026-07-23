import json
import os
import re
import unicodedata
from typing import Any, Dict

import httpx


LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = unicodedata.normalize("NFKD", text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    LLMs sometimes return text around JSON.
    This tries to extract the JSON object safely.
    """
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in LLM response.")

    return json.loads(match.group(0))


def build_job_extraction_prompt(job_text: str) -> str:
    return f"""
You are an AI information extraction engine for a recruitment matching platform.

Extract structured information from the following job offer.

Return ONLY valid JSON. No markdown. No explanation outside JSON.

JSON schema:
{{
  "title": string,
  "company": string | null,
  "location": string | null,
  "contract_type": string | null,
  "language": string,
  "summary": string,
  "technical_skills": [string],
  "tools": [string],
  "databases": [string],
  "methodologies": [string],
  "soft_skills": [string],
  "responsibilities": [string],
  "experience_required": string | null,
  "education_required": string | null,
  "missing_or_unclear_information": [string],
  "english_translation": string
}}

Important rules:
- Extract skills even if the offer is in French, Arabic, or mixed language.
- Extract BOTH required and appreciated/optional skills.
- If a skill appears in a phrase like "would be appreciated", "serait appréciée", "atout", or "plus", still extract it.
- Put technologies, programming languages, frameworks, platforms, and technical concepts in "technical_skills".
- Put software tools and platforms in "tools".
- Put databases in "databases".
- Put practices such as Agile, Scrum, CI/CD, DevOps, testing, deployment, maintenance, documentation in "methodologies".
- Normalize skill names, e.g. "bases de données relationnelles" can imply "Relational databases".
- Keep specific technologies like WinDev, WebDev, SQL Server, MySQL, PostgreSQL, Oracle, Git, SVN, Docker, CI/CD, DevOps.
- Do not hide Docker, CI/CD, or DevOps inside responsibilities only. They must also appear in the correct skills/tools/methodologies lists.
- If company, location, or contract type are not present, return null.
- Do not invent technologies that are not present or clearly implied.
- The english_translation should translate the main job offer content, not every tiny detail.
Job offer:
\"\"\"
{job_text}
\"\"\"
""".strip()


def build_cv_extraction_prompt(cv_text: str) -> str:
    return f"""
You are an AI information extraction engine for a recruitment matching platform.

Extract structured information from the following candidate CV/profile.

Return ONLY valid JSON. No markdown. No explanation outside JSON.

JSON schema:
{{
  "full_name": string | null,
  "email": string | null,
  "phone": string | null,
  "language": string,
  "summary": string,
  "technical_skills": [string],
  "tools": [string],
  "databases": [string],
  "methodologies": [string],
  "soft_skills": [string],
  "projects": [string],
  "education": [string],
  "experience": [string],
  "certifications": [string],
  "english_translation": string
}}

Important rules:
- Extract skills even if the CV is in French.
- Normalize skill names.
- Do not invent experience or skills.
- If a field is missing, return null or an empty list.
- The english_translation should summarize the CV/profile in English.

CV/profile:
\"\"\"
{cv_text}
\"\"\"
""".strip()


def mock_extract_job(job_text: str) -> Dict[str, Any]:
    """
    Fallback extraction without real LLM.
    This is not the final intelligence; it is only for testing when no local LLM is running.
    """
    normalized = normalize_text(job_text)
    lower = normalized.lower()

    known_skills = [
        "windev", "webdev", "sql server", "mysql", "postgresql", "oracle",
        "git", "svn", "agile", "docker", "ci/cd", "devops",
        "python", "java", "javascript", "typescript", "react", "fastapi",
        "node.js", "kubernetes", "aws", "linux", "jenkins", "terraform",
        "ansible", "mongodb", "machine learning", "nlp"
    ]

    detected = []
    for skill in known_skills:
        if skill in lower:
            detected.append(skill)

    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    title = lines[0] if lines else "Imported job offer"

    return {
        "title": title[:120],
        "company": None,
        "location": None,
        "contract_type": None,
        "language": "fr" if any(w in lower for w in ["vous", "développement", "compétences", "profil"]) else "unknown",
        "summary": normalized[:500],
        "technical_skills": detected,
        "tools": [s for s in detected if s in ["git", "svn", "docker", "jenkins"]],
        "databases": [s for s in detected if s in ["sql server", "mysql", "postgresql", "oracle", "mongodb"]],
        "methodologies": [s for s in detected if s in ["agile", "ci/cd", "devops"]],
        "soft_skills": [],
        "responsibilities": [],
        "experience_required": None,
        "education_required": None,
        "missing_or_unclear_information": [],
        "english_translation": "Mock mode: enable Ollama or OpenAI for a full translation."
    }


def mock_extract_cv(cv_text: str) -> Dict[str, Any]:
    normalized = normalize_text(cv_text)
    lower = normalized.lower()

    known_skills = [
        "python", "java", "javascript", "typescript", "react", "fastapi",
        "node.js", "docker", "kubernetes", "aws", "linux", "git",
        "github actions", "jenkins", "terraform", "ansible", "postgresql",
        "mysql", "mongodb", "machine learning", "nlp", "devops", "ci/cd"
    ]

    detected = [skill for skill in known_skills if skill in lower]

    return {
        "full_name": None,
        "email": None,
        "phone": None,
        "language": "unknown",
        "summary": normalized[:500],
        "technical_skills": detected,
        "tools": [],
        "databases": [],
        "methodologies": [],
        "soft_skills": [],
        "projects": [],
        "education": [],
        "experience": [],
        "certifications": [],
        "english_translation": "Mock mode: enable Ollama or OpenAI for a full translation."
    }


async def call_ollama(prompt: str) -> str:
    url = f"{OLLAMA_BASE_URL}/api/generate"

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1
        }
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")


async def extract_job_with_ai(job_text: str) -> Dict[str, Any]:
    job_text = normalize_text(job_text)

    if LLM_PROVIDER == "mock":
        return mock_extract_job(job_text)

    if LLM_PROVIDER == "ollama":
        prompt = build_job_extraction_prompt(job_text)
        raw = await call_ollama(prompt)
        return extract_json_from_text(raw)

    raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")

async def extract_cv_with_ai(cv_text: str) -> Dict[str, Any]:
    cv_text = normalize_text(cv_text)

    if LLM_PROVIDER == "mock":
        return enrich_extraction_result(mock_extract_cv(cv_text))

    if LLM_PROVIDER == "ollama":
        prompt = build_cv_extraction_prompt(cv_text)
        raw = await call_ollama(prompt)
        data = extract_json_from_text(raw)
        return enrich_extraction_result(data)

    raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")

def enrich_extraction_result(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adds a unified_skills field combining technical_skills, tools,
    databases, and methodologies. This is used by the matching engine.
    """
    skill_fields = [
        "technical_skills",
        "tools",
        "databases",
        "methodologies"
    ]

    unified = []

    for field in skill_fields:
        values = data.get(field) or []
        if isinstance(values, list):
            for value in values:
                if isinstance(value, str) and value.strip():
                    normalized = value.strip()
                    if normalized.lower() not in [x.lower() for x in unified]:
                        unified.append(normalized)

    data["unified_skills"] = unified
    return data