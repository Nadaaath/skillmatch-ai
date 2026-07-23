# SkillMatch AI Pro v2

AI-powered recruitment and career guidance platform.

## Stack

- React + Vite + Tailwind frontend
- FastAPI backend
- PostgreSQL database
- JWT authentication + RBAC candidate/recruiter/admin
- CV PDF parsing
- Skill extraction
- Hybrid matching engine
- Skill-gap roadmap
- LLM Career Agent with mock/OpenAI/Ollama mode
- External Job Offer Analyzer with manual fallback
- Docker Compose startup

## New in Pro v2

### External Job Offer Analyzer

Candidates and recruiters can paste a public job-offer URL or paste the job description manually. The backend tries a single respectful public-page extraction. If a site blocks extraction, requires login, or returns incomplete content, the user can paste the description manually.

The app then:

- extracts job title/description when available
- detects required skills
- saves the offer
- computes compatibility for the current candidate when possible
- shows matched skills, missing skills, and roadmap

Compliance note: the app does not scrape candidate profiles and does not automate LinkedIn activity. Manual fallback is the expected path for protected platforms.

## Quick start

```powershell
Copy-Item .env.example .env
docker compose down -v
docker compose up --build
```

Frontend: http://localhost:5173  
Backend docs: http://localhost:8000/docs

## Demo flow

1. Register as candidate.
2. Upload a CV PDF.
3. Seed demo jobs.
4. Paste an external job link or job description in the Job Offer Analyzer.
5. Check score, matched skills, missing skills, and roadmap.
6. Ask the AI agent for match explanation/interview questions.
7. Register as recruiter.
8. Create/import offers and rank candidates.

## LLM options

Default mode is mock, so the app works without a paid key.

```env
LLM_PROVIDER=mock
```

Ollama:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=mistral
```

OpenAI-compatible:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

## Next upgrades

- Qdrant vector database for RAG over CVs and job offers.
- Real sentence-transformers embeddings.
- Interview simulator with candidate answer + AI feedback.
- GitHub Actions CI/CD.
- Kubernetes Minikube manifests.
