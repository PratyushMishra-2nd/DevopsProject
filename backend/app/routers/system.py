from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db

router = APIRouter(tags=["system"])


@router.get("/")
def root() -> dict:
    s = get_settings()
    return {"service": s.app_name, "docs": "/docs", "health": "/health", "ready": "/ready", "metrics": "/metrics"}


@router.get("/health")
def health() -> dict:
    """Liveness: the process is up. Deliberately does not touch the database."""
    return {"status": "UP"}


@router.get("/ready")
def ready(db: Session = Depends(get_db)) -> JSONResponse:
    """Readiness: the database answers and (in deployed environments) the schema is migrated."""
    try:
        db.execute(text("SELECT 1"))
        if get_settings().require_migrations:
            version = db.execute(text("SELECT version_num FROM alembic_version")).scalar()
            if not version:
                return JSONResponse({"status": "NOT_READY", "reason": "schema not migrated"}, status_code=503)
    except SQLAlchemyError as exc:
        return JSONResponse(
            {"status": "NOT_READY", "reason": type(exc).__name__},
            status_code=503,
        )
    return JSONResponse({"status": "READY"})


@router.get("/api/info")
def info() -> dict:
    s = get_settings()
    return {"service": s.app_name, "environment": s.app_env, "git_sha": s.git_sha}
