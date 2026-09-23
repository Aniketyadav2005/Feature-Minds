"""
FastAPI application entrypoint — wires up CORS, static file serving,
DB table creation, and each feature's router.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, engine

from app.features.auth.router import router as auth_router
from app.features.analyze.router import router as analyze_router
from app.features.history.router import router as history_router
from app.features.research.router import router as research_router
from app.features.export.router import router as export_router

# Import models so SQLAlchemy knows about them before create_all()
from app.models.user import User
from app.models.analysis import AnalysisResult, GroundTruth


# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)


# --------------------------------------------------
# Settings
# --------------------------------------------------

settings = get_settings()


# --------------------------------------------------
# FastAPI Application
# --------------------------------------------------

app = FastAPI(
    title="Meme Hate Speech Detector API",
    description="Backend for the meme captioning / OCR / hate-speech detection pipeline.",
    version="1.0.0",
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Static Files
# --------------------------------------------------

# Serve saved and blurred images to the Angular frontend
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)


# --------------------------------------------------
# Routers
# --------------------------------------------------

app.include_router(auth_router)
app.include_router(analyze_router)
app.include_router(history_router)
app.include_router(research_router)
app.include_router(export_router)


# --------------------------------------------------
# Startup
# --------------------------------------------------

@app.on_event("startup")
def on_startup():
    """
    Create database tables for local/development use.

    For production, prefer Alembic migrations.
    """
    Base.metadata.create_all(bind=engine)


# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.get("/api/health")
def health_check():
    return {"status": "ok"}