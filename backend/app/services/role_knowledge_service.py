import csv
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid5, NAMESPACE_URL

from app.services.vector_store import index_document, search_documents


DATASET_PATH = Path(__file__).resolve().parents[1] / "data" / "IT_Job_Roles_Skills.csv"


def _split_list(value: str | None) -> List[str]:
    if not value:
        return []

    separators = [",", ";", "|"]
    items = [value]

    for sep in separators:
        if sep in value:
            items = value.split(sep)
            break

    cleaned = []

    for item in items:
        item = item.strip()
        if item and item.lower() not in [x.lower() for x in cleaned]:
            cleaned.append(item)

    return cleaned

def load_role_dataset() -> List[Dict[str, Any]]:
    """
    Loads the IT role dataset from CSV.
    Expected columns:
    - Job Title
    - Job Description
    - Skills
    - Certifications
    """
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")

    rows = []
    last_error = None

    # Some CSV files exported from Excel use cp1252 instead of UTF-8.
    possible_encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]

    for encoding in possible_encodings:
        try:
            with DATASET_PATH.open("r", encoding=encoding, newline="") as file:
                reader = csv.DictReader(file)

                for idx, row in enumerate(reader):
                    title = (row.get("Job Title") or "").strip()
                    description = (row.get("Job Description") or "").strip()
                    skills_raw = row.get("Skills") or ""
                    certs_raw = row.get("Certifications") or ""

                    if not title:
                        continue

                    skills = _split_list(skills_raw)
                    certifications = _split_list(certs_raw)

                    rows.append(
                        {
                            "row_id": idx,
                            "title": title,
                            "description": description,
                            "skills": skills,
                            "certifications": certifications,
                            "raw_skills": skills_raw,
                            "raw_certifications": certs_raw,
                        }
                    )

            return rows

        except UnicodeDecodeError as exc:
            rows = []
            last_error = exc
            continue

    raise UnicodeDecodeError(
        "csv",
        b"",
        0,
        1,
        f"Could not decode dataset with supported encodings. Last error: {last_error}",
    )

def build_role_text(role: Dict[str, Any]) -> str:
    return f"""
IT Role: {role["title"]}

Description:
{role.get("description") or ""}

Expected skills:
{", ".join(role.get("skills") or [])}

Recommended certifications:
{", ".join(role.get("certifications") or [])}
""".strip()


def index_roles_dataset() -> Dict[str, Any]:
    """
    Indexes all dataset roles into Qdrant as doc_type='role'.
    This makes the dataset searchable by semantic meaning.
    """
    roles = load_role_dataset()
    indexed = 0

    for role in roles:
        role_text = build_role_text(role)
        stable_point_id = str(uuid5(NAMESPACE_URL, f"skillmatch-role-{role['row_id']}-{role['title']}"))

        index_document(
            text=role_text,
            doc_type="role",
            metadata={
                "source_id": f"role-{role['row_id']}",
                "role_id": role["row_id"],
                "title": role["title"],
                "skills": role["skills"],
                "certifications": role["certifications"],
            },
            point_id=stable_point_id,
        )

        indexed += 1

    return {
        "dataset_path": str(DATASET_PATH),
        "roles_loaded": len(roles),
        "roles_indexed": indexed,
    }


def search_roles(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Searches closest IT roles from the dataset using Qdrant.
    """
    return search_documents(
        query=query,
        limit=limit,
        doc_type="role",
    )


def recommend_from_roles(
    job_text: str,
    candidate_skills: List[str] | None = None,
    limit: int = 5,
) -> Dict[str, Any]:
    """
    Finds closest IT roles and recommends skills/certifications.
    """
    candidate_skills = candidate_skills or []
    candidate_lower = {skill.lower() for skill in candidate_skills}

    role_results = search_roles(job_text, limit=limit)

    aggregated_skills = []
    aggregated_certs = []
    closest_roles = []

    for result in role_results:
        payload = result.get("payload") or {}

        role_title = payload.get("title")
        role_skills = payload.get("skills") or []
        role_certs = payload.get("certifications") or []

        closest_roles.append(
            {
                "title": role_title,
                "score": result.get("score"),
                "skills": role_skills,
                "certifications": role_certs,
            }
        )

        for skill in role_skills:
            if skill and skill.lower() not in [x.lower() for x in aggregated_skills]:
                aggregated_skills.append(skill)

        for cert in role_certs:
            if cert and cert.lower() not in [x.lower() for x in aggregated_certs]:
                aggregated_certs.append(cert)

    missing_skills = [
        skill for skill in aggregated_skills
        if skill.lower() not in candidate_lower
    ]

    return {
        "closest_roles": closest_roles,
        "recommended_skills": aggregated_skills[:20],
        "missing_skills": missing_skills[:15],
        "recommended_certifications": aggregated_certs[:10],
    }