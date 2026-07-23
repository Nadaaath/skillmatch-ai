import json
import os
import re
from typing import Any, Dict

import httpx


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")


async def generate_text(prompt: str) -> str:
    """
    Main LLM abstraction.

    Priority:
    - If LLM_PROVIDER=ollama -> use Ollama
    - If LLM_PROVIDER=gemini -> try Gemini, then fallback to Ollama if Gemini fails
    - If LLM_PROVIDER=mock -> return mock response
    """
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "ollama":
        return await _call_ollama(prompt)

    if provider == "gemini":
        try:
            return await _call_gemini(prompt)
        except Exception as gemini_error:
            print(f"[LLM] Gemini failed, falling back to Ollama: {gemini_error}")
            return await _call_ollama(prompt)

    if provider == "mock":
        return "Mock LLM response. Configure LLM_PROVIDER=ollama or LLM_PROVIDER=gemini."

    raise RuntimeError(f"Unsupported LLM_PROVIDER: {provider}")


async def generate_json(prompt: str) -> Dict[str, Any]:
    raw = await generate_text(prompt)
    return extract_json(raw)


async def _call_ollama(prompt: str) -> str:
    base_url = os.getenv("OLLAMA_BASE_URL", OLLAMA_BASE_URL)
    model = os.getenv("OLLAMA_MODEL", OLLAMA_MODEL)

    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                },
            },
        )

        response.raise_for_status()
        return response.json().get("response", "")


async def _call_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
    model = os.getenv("GEMINI_MODEL", GEMINI_MODEL)

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    from google import genai

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    return response.text or ""


def extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found in LLM response.")

    return json.loads(match.group(0))