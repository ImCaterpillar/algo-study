from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine, SessionLocal
from .seed import seed_database
from .migrations import migrate_sqlite_database
from .config import CORS_ORIGINS
from .routes import problems, submissions, notes, reviews, templates, stats, execute, ai, sandbox, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    migrate_sqlite_database()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(title="AlgoStudy API", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"name": "AlgoStudy", "message": "Personal algorithm learning system is running."}


@app.get("/health")
def health_check():
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok", "version": app.version}

app.include_router(auth.router, prefix="/api")
app.include_router(problems.router, prefix="/api")
app.include_router(submissions.router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(templates.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(execute.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(sandbox.router, prefix="/api")
