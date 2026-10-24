"""Dashboard endpoint (separate from account for clarity)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session, principal
from app.core.security import AuthPrincipal
from app.services import account_service

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(session: Session = Depends(db_session), user: AuthPrincipal = Depends(principal)) -> dict:
    return account_service.dashboard_summary(session, user.user_id)
