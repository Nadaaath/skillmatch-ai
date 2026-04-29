from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routes.candidate import router as candidate_router
from routes.job import router as job_router

app = FastAPI(title="SkillMatch AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "SkillMatch AI backend is running"}

app.include_router(candidate_router)
app.include_router(job_router)

# from fastapi import FastAPI, Depends
# from fastapi.middleware.cors import CORSMiddleware
# from sqlalchemy.orm import Session
# from sqlalchemy.exc import IntegrityError

# from database import Base, engine, get_db
# import models

# from routes.candidate import router as candidate_router
# from routes.job import router as job_router

# app = FastAPI(title="SkillMatch AI")

# # ✅ CORS so React (5173) can call FastAPI (8000)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ✅ Create tables
# Base.metadata.create_all(bind=engine)

# @app.get("/")
# def root():
#     return {"message": "SkillMatch AI backend is running"}

# # ✅ Routers
# app.include_router(candidate_router)
# app.include_router(job_router)

# # ✅ SAFE seed: can be called many times without crashing
# @app.post("/seed-demo")
# def seed_demo(db: Session = Depends(get_db)):
#     # -------- Candidate (get or create by email) --------
#     candidate = db.query(models.Candidate).filter(models.Candidate.email == "demo@skillmatch.ai").first()

#     if not candidate:
#         candidate = models.Candidate(
#             full_name="Demo Candidate",
#             email="demo@skillmatch.ai",
#             experience_years=2.0,
#             soft_skill_score=4.0,
#             technical_skills="python,sql,git",
#             cv_text=None,
#         )
#         db.add(candidate)






# #==============================
# #for testing easily 
#     # -------- Job (get or create by title) --------
#     job = db.query(models.Job).filter(models.Job.title == "Junior Backend Developer").first()

#     if not job:
#         job = models.Job(
#             title="Junior Backend Developer",
#             required_skills="python,fastapi,sql,docker,gitlab,ci/cd,github"
#         )
#         db.add(job)

#     # Commit safely
#     try:
#         db.commit()
#     except IntegrityError:
#         db.rollback()

#     db.refresh(candidate)
#     db.refresh(job)

#     return {
#         "message": "Demo data ready",
#         "candidate_id": candidate.id,
#         "job_id": job.id
#     }
# #===========