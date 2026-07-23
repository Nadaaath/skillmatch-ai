import json
import re
from typing import Any, Dict, List

from app.services.llm_service import generate_text

def _extract_json(text: str) -> Dict[str, Any]:
    """
    Extracts JSON from an LLM response.
    Ollama can sometimes return text around JSON, so this keeps it safe.
    """
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found in LLM response.")

    return json.loads(match.group(0))


def _fallback_questions(job_title: str, candidate_skills: List[str], missing_skills: List[str]) -> Dict[str, Any]:
    main_skill = candidate_skills[0] if candidate_skills else "your main technical skill"
    gap_skill = missing_skills[0] if missing_skills else "a technology required by the role"

    return {
        "job_title": job_title,
        "questions": {
            "technical": [
                f"Can you explain a project where you used {main_skill}?",
                "How would you design a REST API for a production application?",
                "How do you ensure code quality, performance, and security in a backend project?",
            ],
            "behavioral": [
                "Tell me about a time you had to learn a new technology quickly.",
                "Describe a situation where you worked with a team under a deadline.",
            ],
            "skills_gap": [
                f"This role may require {gap_skill}. How would you learn it quickly?",
                "What would you do during your first two weeks to become productive in this role?",
            ],
            "motivational": [
                f"Why are you interested in the {job_title} position?"
            ],
        },
        "source": "fallback",
    }


async def generate_interview_questions(
    job_title: str,
    job_description: str,
    candidate_name: str,
    candidate_skills: List[str],
    matched_skills: List[str],
    missing_skills: List[str],
) -> Dict[str, Any]:
    """
    Interview Agent:
    Generates personalized technical, behavioral, skills-gap, and motivational questions.
    """

    prompt = f"""
You are an expert technical recruiter and interview coach.

Generate personalized interview questions for the candidate and target job.

Return ONLY valid JSON. No markdown.

JSON schema:
{{
  "job_title": string,
  "questions": {{
    "technical": [string, string, string],
    "behavioral": [string, string],
    "skills_gap": [string, string],
    "motivational": [string]
  }},
  "interview_strategy": string,
  "expected_focus_areas": [string]
}}

Rules:
- Generate exactly 8 questions:
  - 3 technical
  - 2 behavioral
  - 2 skills_gap
  - 1 motivational
- Questions must be specific to the job and candidate.
- Use the missing skills to create realistic gap questions.
- Avoid generic questions when possible.
- The output must be valid JSON.

Candidate:
Name: {candidate_name}
Skills: {candidate_skills}

Matched skills:
{matched_skills}

Missing or weak skills:
{missing_skills}

Target job:
Title: {job_title}
Description:
{job_description}
""".strip()

    try:
        raw = await generate_text(prompt)
        data = _extract_json(raw)
        data["source"] = "ollama"
        return data
    except Exception as exc:
        fallback = _fallback_questions(job_title, candidate_skills, missing_skills)
        fallback["error"] = str(exc)
        return fallback


def _fallback_evaluation(answer: str) -> Dict[str, Any]:
    word_count = len(answer.split())

    if word_count < 15:
        score = 3
        level = "Needs Improvement"
        feedback = "The answer is too short. Add concrete details, explain your actions, and mention results."
    elif word_count < 50:
        score = 6
        level = "Average"
        feedback = "The answer is understandable, but it needs more structure and stronger examples."
    else:
        score = 8
        level = "Good"
        feedback = "The answer is detailed. Improve it further by using the STAR method and adding measurable impact."

    return {
        "score": score,
        "level": level,
        "feedback": feedback,
        "strengths": ["Clear attempt to answer the question"],
        "improvements": [
            "Use the STAR method: Situation, Task, Action, Result",
            "Add a concrete project example",
            "Mention tools, technologies, and measurable impact",
        ],
        "better_answer_suggestion": "Structure your answer with a short context, your exact role, the technical actions you took, and the final result.",
        "source": "fallback",
    }


async def evaluate_interview_answer(
    question: str,
    answer: str,
    job_title: str,
    job_description: str,
    candidate_skills: List[str],
) -> Dict[str, Any]:
    """
    Interview Agent:
    Evaluates a candidate answer and gives score + feedback.
    """

    prompt = f"""
You are an expert technical interviewer.

Evaluate the candidate's answer for the following interview question.

Return ONLY valid JSON. No markdown.

JSON schema:
{{
  "score": number,
  "level": string,
  "feedback": string,
  "strengths": [string],
  "improvements": [string],
  "better_answer_suggestion": string
}}

Scoring:
- 0-3: weak answer
- 4-6: average answer
- 7-8: good answer
- 9-10: excellent answer

Evaluation criteria:
- relevance to the question
- technical accuracy
- clarity
- structure
- concrete examples
- relation to the target job

Target job:
{job_title}

Job description:
{job_description}

Candidate skills:
{candidate_skills}

Question:
{question}

Candidate answer:
{answer}
""".strip()

    try:
        raw = await generate_text(prompt)
        data = _extract_json(raw)
        data["source"] = "ollama"
        return data
    except Exception as exc:
        fallback = _fallback_evaluation(answer)
        fallback["error"] = str(exc)
        return fallback