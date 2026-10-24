"""Spending endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import db_session, principal
from app.core.security import AuthPrincipal
from app.services import spending_service

router = APIRouter(prefix="/api/v1/spending", tags=["spending"])


@router.get("/monthly")
def monthly(session: Session = Depends(db_session), user: AuthPrincipal = Depends(principal), month: str | None = Query(None)) -> dict:
    return spending_service.monthly_spending(session, user.user_id, month)


@router.get("/categories")
def categories(session: Session = Depends(db_session), user: AuthPrincipal = Depends(principal), month: str | None = Query(None)) -> dict:
    return spending_service.category_summary(session, user.user_id, month)
