import os
import httpx
from typing import Any

SYSTEM_PROMPT = """
You are SkillMatch Career Agent, an AI assistant integrated into an intelligent recruitment platform.
Your role is to explain candidate-job matches, detect missing skills, recommend learning actions,
generate interview questions, help recruiters evaluate candidates fairly, and improve job descriptions.
Base your answer only on the context provided. Do not invent skills or experience.
Be practical, structured, and concise.
""".strip()

def build_prompt(message: str, context: dict[str, Any]) -> str:
    return f"""
{SYSTEM_PROMPT}

Context:
{context}

User request:
{message}

Answer:
""".strip()

async def call_llm(prompt: str) -> str:
    provider = os.getenv("LLM_PROVIDER", "mock").lower()

    if provider == "mock":
        return mock_response(prompt)

    if provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
        model = os.getenv("OLLAMA_MODEL", "mistral")
        async with httpx.AsyncClient(timeout=90) as client:
            res = await client.post(
                f"{base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
            )
            res.raise_for_status()
            return res.json().get("response", "")

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if not api_key:
            return "OPENAI_API_KEY is not configured. Set it in .env or use LLM_PROVIDER=mock."
        async with httpx.AsyncClient(timeout=90) as client:
            res = await client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                },
            )
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]

    return f"Unknown LLM_PROVIDER: {provider}"

def mock_response(prompt: str) -> str:
    lower = prompt.lower()
    if "interview" in lower:
        return (
            "Here are personalized interview questions:\n"
            "1. Explain the most relevant projects in your CV for this offer.\n"
            "2. Which required skills do you already master and how did you use them?\n"
            "3. How would you close the missing-skill gaps for this position?\n"
            "4. Describe a technical problem you solved and your approach.\n"
            "5. What would you learn first during your first month in this role?"
        )
    if "improve" in lower or "cv" in lower:
        return (
            "CV improvement suggestions:\n"
            "- Add measurable project results and technologies used.\n"
            "- Make missing but relevant skills visible if you have practiced them.\n"
            "- Add one project aligned with the target job.\n"
            "- Use keywords from the job offer naturally in the experience section."
        )
    return (
        "Based on the matching context, the candidate is recommended because the profile shares several key skills with the job. "
        "The main improvement area is to close the missing-skill gap through a targeted project and update the CV with concrete evidence."
    )

async def generate_agent_response(message: str, context: dict[str, Any]) -> str:
    prompt = build_prompt(message, context)
    return await call_llm(prompt)
