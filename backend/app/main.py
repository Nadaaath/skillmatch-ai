import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine, SessionLocal
from . import models
from app.routes import auth, candidates, jobs, matching, agent, analytics, ai, rag, recommendations, roles, skills_gap, interview, agentic, llm, scraping
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SkillMatch AI API",
    description="AI-powered candidate-job matching platform with an LLM career agent.",
    version="0.1.0",
)

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(candidates.router)
app.include_router(jobs.router)
app.include_router(matching.router)
app.include_router(agent.router)
app.include_router(analytics.router)
app.include_router(ai.router)
app.include_router(rag.router)
app.include_router(recommendations.router)
app.include_router(roles.router)
app.include_router(skills_gap.router)
app.include_router(interview.router)
app.include_router(agentic.router)
app.include_router(llm.router)
app.include_router(scraping.router)

@app.get("/")
def root():
    return {"message": "SkillMatch AI API is running"}


@app.post("/seed")
def seed_demo_data():
    db = SessionLocal()

    try:
        if db.query(models.Job).count() == 0:
            jobs = [
                models.Job(
                    title="Backend Developer Intern",
                    company="TechCorp",
                    description="Build REST APIs with Python, FastAPI, PostgreSQL, Docker and Git. Experience with React is a plus.",
                    required_skills=["python", "fastapi", "postgresql", "docker", "git", "api"],
                    location="Rabat",
                    contract_type="Internship",
                ),
                models.Job(
                    title="Junior DevOps Engineer",
                    company="CloudOps Maroc",
                    description="Deploy applications using Docker, Kubernetes, Linux, CI/CD, GitHub Actions and cloud platforms such as AWS.",
                    required_skills=["docker", "kubernetes", "linux", "ci/cd", "github actions", "aws"],
                    location="Casablanca",
                    contract_type="Internship",
                ),
                models.Job(
                    title="AI/NLP Engineer Intern",
                    company="AI Lab",
                    description="Work on NLP, machine learning, sentence-transformers, RAG, LLM applications and vector databases such as Qdrant.",
                    required_skills=["python", "machine learning", "nlp", "llm", "rag", "qdrant"],
                    location="Remote",
                    contract_type="Internship",
                ),
                models.Job(
                    title="Cloud DevOps Intern",
                    company="InfraLab",
                    description="Create CI/CD pipelines, containerize apps, deploy to Kubernetes, monitor with Prometheus and Grafana, and document infrastructure decisions.",
                    required_skills=["docker", "kubernetes", "ci/cd", "github actions", "prometheus", "grafana", "linux"],
                    location="Rabat",
                    contract_type="PFA Internship",
                ),
                models.Job(
                    title="Full-Stack AI Product Intern",
                    company="Startup Studio",
                    description="Build React dashboards, FastAPI endpoints, PostgreSQL schemas, and LLM-powered features for candidate-job matching.",
                    required_skills=["react", "fastapi", "postgresql", "python", "llm", "api"],
                    location="Hybrid",
                    contract_type="Internship",
                ),
            ]

            db.add_all(jobs)
            db.commit()

        return {"message": "Demo data seeded"}

    finally:
        db.close()