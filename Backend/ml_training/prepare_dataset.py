import pandas as pd
import numpy as np

# =========================
# CONFIG
# =========================
DATA_PATH = "ml_training/data/resumes.csv"
OUTPUT_PATH = "ml_training/data/processed_dataset.csv"

REQUIRED_SKILLS = [
    "python", "java", "javascript", "react",
    "fastapi", "flask", "sql", "docker", "git"
]


# =========================
# HELPERS
# =========================
def normalize_skills(skill_string):
    if pd.isna(skill_string):
        return []
    return [s.strip().lower() for s in skill_string.split(",")]


def skill_match_ratio(candidate_skills, required_skills):
    if not required_skills:
        return 0.0
    return len(set(candidate_skills) & set(required_skills)) / len(required_skills)


# =========================
# LOAD DATA
# =========================
df = pd.read_csv(DATA_PATH)

print("Original columns:")
print(df.columns)

# =========================
# CLEAN & FEATURE ENGINEERING
# =========================

# Normalize skills
df["skills_list"] = df["Skills"].apply(normalize_skills)

# Skill match ratio (simulated job requirements)
df["skill_match_ratio"] = df["skills_list"].apply(
    lambda skills: skill_match_ratio(skills, REQUIRED_SKILLS)
)

# Experience
df["experience_years"] = df["Experience (Years)"]

# Projects count
df["projects_count"] = df["Projects Count"]

# Certifications count
df["certifications_count"] = df["Certifications"].fillna("").apply(
    lambda x: len(str(x).split(",")) if x else 0
)

# Soft skill score (simulated)
np.random.seed(42)
df["soft_skill_score"] = np.random.uniform(2.5, 5.0, size=len(df))

# TF-IDF similarity score (simulated proxy)
df["tfidf_score"] = np.random.uniform(0.3, 1.0, size=len(df))

# =========================
# TARGET LABEL
# =========================
df["hired"] = df["Recruiter Decision"].apply(
    lambda x: 1 if str(x).lower() == "hire" else 0
)

# =========================
# FINAL DATASET
# =========================
final_df = df[
    [
        "skill_match_ratio",
        "experience_years",
        "projects_count",
        "certifications_count",
        "soft_skill_score",
        "tfidf_score",
        "hired",
    ]
]

print("\nFinal dataset preview:")
print(final_df.head())

# Save processed dataset
final_df.to_csv(OUTPUT_PATH, index=False)

print(f"\n✅ Processed dataset saved to {OUTPUT_PATH}")
