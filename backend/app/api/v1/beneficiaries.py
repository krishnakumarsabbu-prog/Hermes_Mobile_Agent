"""Beneficiary endpoints with user-scoped access."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import db_session, principal
from app.core.security import AuthPrincipal
from app.services import beneficiary_service

router = APIRouter(prefix="/api/v1/beneficiaries", tags=["beneficiaries"])


@router.get("")
def list_beneficiaries(
    session: Session = Depends(db_session),
    user: AuthPrincipal = Depends(principal),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
) -> dict:
    return beneficiary_service.list_beneficiaries(session, user.user_id, {"page": page, "pageSize": pageSize, "search": search})


@router.get("/{beneficiary_id}")
def get_beneficiary(beneficiary_id: str, session: Session = Depends(db_session), user: AuthPrincipal = Depends(principal)) -> dict:
    return beneficiary_service.get_beneficiary(session, user.user_id, beneficiary_id)
