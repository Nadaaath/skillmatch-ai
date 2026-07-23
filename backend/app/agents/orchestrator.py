from typing import Any, Dict, List

from app import models
from app.agents.skills_gap_agent import analyze_skills_gap
from app.agents.interview_agent import generate_interview_questions
from app.services.llm_service import generate_text

def _normalize(items: List[str] | None) -> List[str]:
    if not items:
        return []

    cleaned = []

    for item in items:
        if not item:
            continue

        value = str(item).strip()

        if value and value.lower() not in [x.lower() for x in cleaned]:
            cleaned.append(value)

    return cleaned


def _skill_match(candidate_skills: List[str], job_skills: List[str]) -> Dict[str, Any]:
    candidate_skills = _normalize(candidate_skills)
    job_skills = _normalize(job_skills)

    candidate_lower = {skill.lower() for skill in candidate_skills}

    matched = [
        skill for skill in job_skills
        if skill.lower() in candidate_lower
    ]

    missing = [
        skill for skill in job_skills
        if skill.lower() not in candidate_lower
    ]

    if not job_skills:
        score = 0
    else:
        score = round((len(matched) / len(job_skills)) * 100)

    return {
        "score": score,
        "matched_skills": matched,
        "missing_skills": missing,
    }


async def _generate_agent_explanation(
    candidate: models.Candidate,
    job: models.Job,
    match_result: Dict[str, Any],
    skills_gap: Dict[str, Any],
) -> str:
    prompt = f"""
You are SkillMatch AI, an expert career and recruitment assistant.

Explain the compatibility between this candidate and this job.
Be practical, honest, and specific.
Mention matched skills, missing skills, and what the candidate should do next.

Candidate:
Name: {candidate.full_name}
Skills: {candidate.skills}
CV:
{candidate.cv_text or ""}

Job:
Title: {job.title}
Company: {job.company}
Description:
{job.description}
Required skills:
{job.required_skills}

Match result:
{match_result}

Skills gap and recommendations:
{skills_gap}

Return a clear answer in 3 sections:
1. Match summary
2. Main gaps
3. Action plan
""".strip()

    try:
        return await generate_text(prompt)
    except Exception as exc:
        return (
            "AI explanation could not be generated. "
            f"Fallback summary: score={match_result.get('score')}%, "
            f"matched={match_result.get('matched_skills')}, "
            f"missing={match_result.get('missing_skills')}. "
            f"Error: {exc}"
        )


async def run_full_candidate_job_analysis(
    candidate: models.Candidate,
    job: models.Job,
) -> Dict[str, Any]:
    """
    Full Agentic AI pipeline:
    1. Matching Agent
    2. Skills Gap + Certification Agent
    3. Interview Agent
    4. LLM Explanation Agent
    """

    candidate_skills = _normalize(candidate.skills or [])
    job_skills = _normalize(job.required_skills or [])

    # Agent 1: Matching
    match_result = _skill_match(candidate_skills, job_skills)

    # Agent 2: Skills gap + dataset certifications
    skills_gap = analyze_skills_gap(
        candidate_skills=candidate_skills,
        job_skills=job_skills,
        job_text=job.description or job.title,
    )

    # Agent 3: Interview questions
    interview = await generate_interview_questions(
        job_title=job.title,
        job_description=job.description,
        candidate_name=candidate.full_name,
        candidate_skills=candidate_skills,
        matched_skills=match_result["matched_skills"],
        missing_skills=skills_gap.get("combined_missing_skills", []),
    )

    # Agent 4: Explanation
    ai_explanation = await _generate_agent_explanation(
        candidate=candidate,
        job=job,
        match_result=match_result,
        skills_gap=skills_gap,
    )

    return {
        "pipeline_steps": [
            "matching_agent",
            "skills_gap_agent",
            "interview_agent",
            "explanation_agent",
        ],
        "candidate": {
            "id": candidate.id,
            "name": candidate.full_name,
            "skills": candidate_skills,
        },
        "job": {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "skills": job_skills,
        },
        "match": match_result,
        "skills_gap": skills_gap,
        "interview": interview,
        "ai_explanation": ai_explanation,
    }