import re
from collections import defaultdict

SKILL_CATEGORIES = {
    "Programming": ["python", "java", "javascript", "typescript", "php", "c", "c++", "c#"],
    "Frontend": ["react", "vite", "html", "css", "tailwind", "bootstrap", "next.js"],
    "Backend": ["node.js", "express", "fastapi", "django", "flask", "spring boot", "api", "rest", "graphql", "microservices"],
    "Database": ["postgresql", "mysql", "mongodb", "sql", "redis", "elasticsearch"],
    "DevOps": ["docker", "docker compose", "kubernetes", "git", "github", "github actions", "gitlab ci", "jenkins", "linux", "bash", "ci/cd", "terraform", "ansible", "nginx", "sonarqube", "trivy", "bandit", "gitleaks"],
    "Cloud": ["aws", "azure", "gcp", "cloud", "ec2", "s3", "lambda", "vpc", "iam"],
    "AI / Data": ["machine learning", "deep learning", "nlp", "data science", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "bert", "llm", "rag", "qdrant", "langchain", "langgraph", "lightgbm", "sentence-transformers"],
    "Analytics": ["power bi", "tableau", "excel", "grafana", "prometheus"],
    "Methods": ["agile", "scrum", "security", "oauth", "jwt"],
}

SKILLS = sorted({skill for skills in SKILL_CATEGORIES.values() for skill in skills})

ALIASES = {
    "js": "javascript",
    "ts": "typescript",
    "postgres": "postgresql",
    "k8s": "kubernetes",
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "github action": "github actions",
    "github-actions": "github actions",
    "nodejs": "node.js",
    "rest api": "api",
    "apis": "api",
    "ml": "machine learning",
    "genai": "llm",
    "gen ai": "llm",
}

LEARNING_RESOURCES = {
    "docker": ["Containerize a FastAPI + PostgreSQL app", "Practice Dockerfile and docker-compose.yml", "Add a small README explaining images vs containers"],
    "kubernetes": ["Deploy frontend, backend and PostgreSQL on Minikube", "Create Deployment, Service and ConfigMap YAML files", "Take screenshots of kubectl get pods and services"],
    "aws": ["Deploy one backend service on EC2 or Render as a free alternative", "Review VPC, EC2, S3 and IAM basics", "Document a small cloud deployment diagram"],
    "terraform": ["Create a small IaC folder for one cloud resource", "Explain variables, providers and state in the report"],
    "fastapi": ["Build protected REST endpoints with Pydantic schemas", "Add Swagger screenshots from /docs", "Write pytest tests for two endpoints"],
    "postgresql": ["Model users, candidates, jobs and matches", "Use JSONB-like skill fields", "Add realistic seed data"],
    "react": ["Create separate candidate and recruiter spaces", "Add reusable cards, badges and match progress bars"],
    "llm": ["Build an agent with explain-match, CV feedback and interview modes", "Use strict prompts that only use provided context"],
    "rag": ["Store CV/job embeddings in Qdrant", "Retrieve relevant jobs before asking the LLM", "Explain the RAG flow in one architecture diagram"],
    "qdrant": ["Run Qdrant in Docker Compose", "Create collections for candidates and jobs", "Search top-k similar profiles/offers"],
    "github actions": ["Add workflow for backend tests and docker build", "Show green pipeline screenshot in report"],
    "ci/cd": ["Automate lint/test/build steps", "Document pipeline stages clearly"],
}

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()

def extract_skills(text: str) -> list[str]:
    normalized = normalize_text(text)
    found = set()
    for alias, canonical in ALIASES.items():
        if re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", normalized):
            found.add(canonical)
    for skill in SKILLS:
        pattern = rf"(?<![a-z0-9]){re.escape(skill.lower())}(?![a-z0-9])"
        if re.search(pattern, normalized):
            found.add(skill)
    return sorted(found)

def categorize_skills(skills: list[str]) -> dict[str, list[str]]:
    result = defaultdict(list)
    normalized = {s.lower(): s for s in skills or []}
    for category, category_skills in SKILL_CATEGORIES.items():
        for s in category_skills:
            if s in normalized:
                result[category].append(normalized[s])
    uncategorized = [s for s in skills or [] if not any(s in vals for vals in result.values())]
    if uncategorized:
        result["Other"] = uncategorized
    return dict(result)

def build_learning_plan(missing_skills: list[str]) -> list[dict]:
    plan = []
    for idx, skill in enumerate(missing_skills or []):
        priority = "high" if idx < 3 else "medium"
        plan.append({
            "skill": skill,
            "priority": priority,
            "actions": LEARNING_RESOURCES.get(skill.lower(), [
                f"Study the basics of {skill}",
                f"Build a small practical mini-project using {skill}",
                f"Add concrete evidence of {skill} to your CV"
            ])
        })
    return plan
