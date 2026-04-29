import os
import re
import joblib
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# =====================================================
# 1. SKILL EXTRACTION (RULE-BASED NLP)
# =====================================================

KNOWN_SKILLS = [
    "python", "java", "javascript", "react", "angular",
    "fastapi", "flask", "django",
    "sql", "mysql", "postgresql",
    "docker", "kubernetes",
    "git", "linux",
    "machine learning", "deep learning"
]


def extract_skills_from_text(text: str):
    """
    Extract technical skills from CV text using keyword matching
    """
    if not text:
        return []

    text = text.lower()
    found_skills = []

    for skill in KNOWN_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text):
            found_skills.append(skill)

    return found_skills


# =====================================================
# 2. TF-IDF SEMANTIC SIMILARITY
# =====================================================

tfidf_vectorizer = TfidfVectorizer(stop_words="english")


def compute_tfidf_similarity(cv_text: str, job_text: str) -> float:
    """
    Compute cosine similarity between CV text and job description
    """
    if not cv_text or not job_text:
        return 0.0

    texts = [cv_text, job_text]
    tfidf_matrix = tfidf_vectorizer.fit_transform(texts)

    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    return float(similarity)


# =====================================================
# 3. SKILL MATCH RATIO
# =====================================================

def compute_skill_match_ratio(candidate_skills: str, job_skills: str):
    if not candidate_skills or not job_skills:
        return 0.0, []

    candidate_set = set(
        s.strip().lower() for s in candidate_skills.split(",")
    )
    job_set = set(
        s.strip().lower() for s in job_skills.split(",")
    )

    matched = candidate_set.intersection(job_set)
    missing = list(job_set - candidate_set)

    ratio = len(matched) / len(job_set) if job_set else 0.0

    return ratio, missing



# =====================================================
# 4. SUPERVISED ML MODEL (LOGISTIC REGRESSION)
# =====================================================

MODEL_PATH = "ml_training/hiring_model.pkl"

hiring_model = None
if os.path.exists(MODEL_PATH):
    hiring_model = joblib.load(MODEL_PATH)


def predict_hiring_probability(features: dict) -> float:
    """
    Predict hiring probability using trained ML model
    """
    if hiring_model is None:
        return 0.0

    df = pd.DataFrame([features])
    probability = hiring_model.predict_proba(df)[0][1]

    return round(float(probability), 3)

