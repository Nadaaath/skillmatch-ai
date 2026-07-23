from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from app import models
from app.agents.skills_gap_agent import analyze_skills_gap
from app.agents.interview_agent import generate_interview_questions
from app.services.llm_service import generate_text


class AgentState(TypedDict, total=False):
    candidate: models.Candidate
    job: models.Job

    candidate_skills: List[str]
    job_skills: List[str]

    match: Dict[str, Any]
    skills_gap: Dict[str, Any]
    interview: Dict[str, Any]
    ai_explanation: str

    pipeline_steps: List[str]
    error: Optional[str]


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

    score = round((len(matched) / len(job_skills)) * 100) if job_skills else 0

    return {
        "score": score,
        "matched_skills": matched,
        "missing_skills": missing,
        "candidate_skills_count": len(candidate_skills),
        "job_skills_count": len(job_skills),
    }


def prepare_node(state: AgentState) -> AgentState:
    candidate = state["candidate"]
    job = state["job"]

    state["candidate_skills"] = _normalize(candidate.skills or [])
    state["job_skills"] = _normalize(job.required_skills or [])
    state["pipeline_steps"] = ["prepare_node"]

    return state


def matching_node(state: AgentState) -> AgentState:
    if state.get("error"):
        return state

    try:
        state["match"] = _skill_match(
            candidate_skills=state.get("candidate_skills", []),
            job_skills=state.get("job_skills", []),
        )

        state["pipeline_steps"].append("matching_node")
        return state

    except Exception as exc:
        state["error"] = f"matching_node failed: {exc}"
        return state


def skills_gap_node(state: AgentState) -> AgentState:
    if state.get("error"):
        return state

    try:
        job = state["job"]

        state["skills_gap"] = analyze_skills_gap(
            candidate_skills=state.get("candidate_skills", []),
            job_skills=state.get("job_skills", []),
            job_text=job.description or job.title,
        )

        state["pipeline_steps"].append("skills_gap_node")
        return state

    except Exception as exc:
        state["error"] = f"skills_gap_node failed: {exc}"
        return state


async def interview_node(state: AgentState) -> AgentState:
    if state.get("error"):
        return state

    try:
        candidate = state["candidate"]
        job = state["job"]
        match = state.get("match", {})
        skills_gap = state.get("skills_gap", {})

        state["interview"] = await generate_interview_questions(
            job_title=job.title,
            job_description=job.description,
            candidate_name=candidate.full_name,
            candidate_skills=state.get("candidate_skills", []),
            matched_skills=match.get("matched_skills", []),
            missing_skills=skills_gap.get("combined_missing_skills", []),
        )

        state["pipeline_steps"].append("interview_node")
        return state

    except Exception as exc:
        state["error"] = f"interview_node failed: {exc}"
        return state


async def explanation_node(state: AgentState) -> AgentState:
    if state.get("error"):
        return state

    try:
        candidate = state["candidate"]
        job = state["job"]

        prompt = f"""
You are SkillMatch AI, an expert career assistant.

Generate a concise but useful compatibility explanation.

Candidate:
Name: {candidate.full_name}
Skills: {state.get("candidate_skills", [])}
CV:
{candidate.cv_text or ""}

Job:
Title: {job.title}
Company: {job.company}
Description:
{job.description}
Required skills:
{state.get("job_skills", [])}

Match:
{state.get("match", {})}

Skills gap:
{state.get("skills_gap", {})}

Return the answer with these sections:
1. Match summary
2. Missing skills
3. Recommended next steps
""".strip()

        state["ai_explanation"] = await generate_text(prompt)
        state["pipeline_steps"].append("explanation_node")
        return state

    except Exception as exc:
        state["error"] = f"explanation_node failed: {exc}"
        return state


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("prepare", prepare_node)
    graph.add_node("matching", matching_node)
    graph.add_node("skills_gap", skills_gap_node)
    graph.add_node("interview", interview_node)
    graph.add_node("explanation", explanation_node)

    graph.set_entry_point("prepare")

    graph.add_edge("prepare", "matching")
    graph.add_edge("matching", "skills_gap")
    graph.add_edge("skills_gap", "interview")
    graph.add_edge("interview", "explanation")
    graph.add_edge("explanation", END)

    return graph.compile()


_graph = None


def get_graph():
    global _graph

    if _graph is None:
        _graph = build_graph()

    return _graph


def _format_response(state: AgentState) -> Dict[str, Any]:
    candidate = state["candidate"]
    job = state["job"]

    return {
        "orchestrator": "langgraph",
        "pipeline_steps": state.get("pipeline_steps", []),
        "error": state.get("error"),
        "candidate": {
            "id": candidate.id,
            "name": candidate.full_name,
            "skills": state.get("candidate_skills", []),
        },
        "job": {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "skills": state.get("job_skills", []),
        },
        "match": state.get("match"),
        "skills_gap": state.get("skills_gap"),
        "interview": state.get("interview"),
        "ai_explanation": state.get("ai_explanation"),
    }


async def run_langgraph_candidate_job_analysis(
    candidate: models.Candidate,
    job: models.Job,
) -> Dict[str, Any]:
    graph = get_graph()

    initial_state: AgentState = {
        "candidate": candidate,
        "job": job,
        "pipeline_steps": [],
        "error": None,
    }

    final_state = await graph.ainvoke(initial_state)

    return _format_response(final_state)