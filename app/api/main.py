"""
Entropi API — application entry point.

Run the server with:
    make api-run
    # or manually:
    uvicorn app.api.main:app --reload

All routes are versioned under /api/v1:
    /api/v1/research/*   — Data ingestion and ML categorization
    /api/v1/file/*       — Template file downloads (no auth required)
    /api/v1/config/*     — Keyword and group management
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import research, file, config

app = FastAPI(
    title="Entropi API",
    description=(
        "REST API for the Entropi research categorization system. "
        "Provides endpoints for data ingestion, ML categorization, "
        "file templates, and keyword configuration management."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_PREFIX = "/api/v1"

app.include_router(research.router, prefix=_PREFIX)
app.include_router(file.router, prefix=_PREFIX)
app.include_router(config.router, prefix=_PREFIX)


@app.get("/health", tags=["Health"])
def health_check():
    """Returns the server status. No authentication required."""
    return {"status": "ok"}
