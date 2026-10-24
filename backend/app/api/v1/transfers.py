"""Transfer endpoints: prepare, authorize, cancel, status."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session, principal, request_id_dep
from app.core.security import AuthPrincipal
from app.schemas.transfer import AuthorizeTransferRequest, PrepareTransferRequest
from app.services import transfer_service

router = APIRouter(prefix="/api/v1/transfers", tags=["transfers"])


@router.post("/prepare")
def prepare(
    body: PrepareTransferRequest,
    session: Session = Depends(db_session),
    user: AuthPrincipal = Depends(principal),
    request_id: str = Depends(request_id_dep),
) -> dict:
    return transfer_service.prepare(
        session,
        user_id=user.user_id,
        beneficiary_id=body.beneficiaryId,
        amount_paise=body.amountPaise,
        currency=body.currency,
        idempotency_key=body.idempotencyKey,
        request_id=request_id,
    )


@router.post("/{approval_id}/authorize")
def authorize(
    approval_id: str,
    body: AuthorizeTransferRequest,
    session: Session = Depends(db_session),
    user: AuthPrincipal = Depends(principal),
    request_id: str = Depends(request_id_dep),
) -> dict:
    return transfer_service.authorize(
        session,
        approval_id=approval_id,
        user_id=user.user_id,
        idempotency_key=body.idempotencyKey,
        request_id=request_id,
    )


@router.post("/{approval_id}/cancel")
def cancel(
    approval_id: str,
    session: Session = Depends(db_session),
    user: AuthPrincipal = Depends(principal),
    request_id: str = Depends(request_id_dep),
) -> dict:
    return transfer_service.cancel(session, approval_id=approval_id, user_id=user.user_id, request_id=request_id)


@router.get("/{approval_id}")
def status(
    approval_id: str,
    session: Session = Depends(db_session),
    user: AuthPrincipal = Depends(principal),
) -> dict:
    return transfer_service.status(session, approval_id=approval_id, user_id=user.user_id)
