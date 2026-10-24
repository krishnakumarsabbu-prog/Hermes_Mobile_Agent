"""Transaction endpoints with pagination and filtering."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import db_session, principal
from app.core.errors import ValidationFailure
from app.core.security import AuthPrincipal
from app.services import transaction_service

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


@router.get("")
def list_transactions(
    session: Session = Depends(db_session),
    user: AuthPrincipal = Depends(principal),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    category: str | None = Query(None),
    status: str | None = Query(None),
    startDate: str | None = Query(None),
    endDate: str | None = Query(None),
    merchant: str | None = Query(None),
    reference: str | None = Query(None),
    sort: str = Query("desc", pattern="^(asc|desc)$"),
) -> dict:
    if startDate and endDate and startDate > endDate:
        raise ValidationFailure("startDate must not be after endDate.")
    params = {
        "page": page, "pageSize": pageSize, "category": category, "status": status,
        "startDate": startDate, "endDate": endDate, "merchant": merchant,
        "reference": reference, "sort": sort,
    }
    return transaction_service.list_transactions(session, user.user_id, params)


@router.get("/{transaction_id}")
def get_transaction(transaction_id: str, session: Session = Depends(db_session), user: AuthPrincipal = Depends(principal)) -> dict:
    return transaction_service.get_transaction(session, user.user_id, transaction_id)
