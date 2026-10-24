"""Health and readiness endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import db_session

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def liveness() -> dict:
    return {"status": "ok"}


@router.get("/ready")
def readiness(session: Session = Depends(db_session)) -> dict:
    try:
        session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "reachable"}
    except Exception:
        return {"status": "degraded", "database": "unreachable"}
