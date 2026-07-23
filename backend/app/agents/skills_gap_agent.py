from typing import Any, Dict, List

from app.services.role_knowledge_service import recommend_from_roles


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


def analyze_skills_gap(
    candidate_skills: List[str],
    job_skills: List[str],
    job_text: str,
) -> Dict[str, Any]:
    """
    Skills Gap Agent:
    - compares candidate skills with job skills
    - retrieves related IT roles from dataset
    - recommends missing skills and certifications
    """

    candidate_skills = _normalize(candidate_skills)
    job_skills = _normalize(job_skills)

    candidate_lower = {skill.lower() for skill in candidate_skills}

    direct_missing = [
        skill for skill in job_skills
        if skill.lower() not in candidate_lower
    ]

    role_recommendations = recommend_from_roles(
        job_text=job_text,
        candidate_skills=candidate_skills,
        limit=5,
    )

    dataset_missing = role_recommendations.get("missing_skills", [])
    certifications = role_recommendations.get("recommended_certifications", [])
    closest_roles = role_recommendations.get("closest_roles", [])

    combined_missing = []

    for skill in direct_missing + dataset_missing:
        if skill and skill.lower() not in [x.lower() for x in combined_missing]:
            combined_missing.append(skill)

    priority_plan = []

    for idx, skill in enumerate(combined_missing[:8], start=1):
        priority = "high" if idx <= 3 else "medium"

        priority_plan.append(
            {
                "skill": skill,
                "priority": priority,
                "recommendation": f"Practice {skill} through a small project related to the target job.",
            }
        )

    return {
        "candidate_skills": candidate_skills,
        "job_skills": job_skills,
        "direct_missing_skills": direct_missing,
        "dataset_missing_skills": dataset_missing,
        "combined_missing_skills": combined_missing[:15],
        "closest_roles": closest_roles,
        "recommended_certifications": certifications[:10],
        "priority_plan": priority_plan,
    }