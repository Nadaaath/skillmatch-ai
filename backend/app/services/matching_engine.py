from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .skill_extractor import extract_skills

def semantic_similarity(text_a: str, text_b: str) -> float:
    docs = [text_a or "", text_b or ""]
    if not docs[0].strip() or not docs[1].strip():
        return 0.0
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(docs)
    return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])

def calculate_match(candidate_text: str, candidate_skills: list[str], job_description: str, required_skills: list[str]) -> dict:
    candidate_set = set([s.lower() for s in candidate_skills])
    required_set = set([s.lower() for s in required_skills])

    if not required_set:
        inferred_required = extract_skills(job_description)
        required_set = set([s.lower() for s in inferred_required])
        required_skills = inferred_required

    matched = sorted(candidate_set.intersection(required_set))
    missing = sorted(required_set.difference(candidate_set))

    skill_score = len(matched) / len(required_set) if required_set else 0.0
    sem_score = semantic_similarity(candidate_text, job_description)
    final_score = (0.60 * skill_score) + (0.40 * sem_score)

    explanation = (
        f"The candidate matches {len(matched)} out of {len(required_set)} required skills. "
        f"Matched skills: {', '.join(matched) if matched else 'none'}. "
        f"Missing skills: {', '.join(missing) if missing else 'none'}."
    )

    return {
        "score": round(final_score * 100, 2),
        "skill_score": round(skill_score * 100, 2),
        "semantic_score": round(sem_score * 100, 2),
        "matched_skills": matched,
        "missing_skills": missing,
        "explanation": explanation,
    }
