# SkillMatch AI — Polished Frontend

This frontend is compatible with your current FastAPI backend and includes UI for:

- JWT authentication / RBAC
- Candidate CV upload
- Job analyzer/import
- Rekrute discovery
- Match Lab showing only the current match
- LangGraph full AI career report
- Interview answer evaluation
- RAG Agent
- AI system status

## Install

```powershell
docker compose down
Rename-Item frontend frontend_old
```

Extract this ZIP, rename the extracted folder to `frontend`, then run:

```powershell
docker compose build frontend
docker compose up
```

Open: http://localhost:5173

Expected backend: http://localhost:8000
