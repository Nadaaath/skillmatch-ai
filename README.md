# SkillMatch AI

SkillMatch AI is a full-stack recruitment matching platform that compares candidate CVs with job requirements using AI-based similarity scoring.

## Features

- Candidate profile creation
- PDF CV upload
- Job profile creation
- AI-powered candidate-job matching
- Explainable matching score
- React frontend
- FastAPI backend
- SQLite database

## Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Sentence Transformers / BERT
- PDF text extraction

### Frontend

- React
- Vite
- JavaScript
- CSS


### Run the Backend Locally
cd Backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload

Backend API documentation:

http://localhost:8000/docs
### Run the Frontend Locally

Open another terminal:

cd frontend
npm install
npm run dev

Frontend:

http://localhost:5173
Notes

The backend may take some time to start because the BERT/Sentence Transformer model is loaded for semantic matching.
