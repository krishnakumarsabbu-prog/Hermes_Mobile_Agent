"""Account and dashboard endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session, principal
from app.core.security import AuthPrincipal
from app.services import account_service

router = APIRouter(prefix="/api/v1", tags=["account"])


@router.get("/dashboard/summary")
def dashboard_summary(session: Session = Depends(db_session), user: AuthPrincipal = Depends(principal)) -> dict:
    return account_service.dashboard_summary(session, user.user_id)


@router.get("/account")
def get_account(session: Session = Depends(db_session), user: AuthPrincipal = Depends(principal)) -> dict:
    account = account_service.account_summary(session, user.user_id)
    return {
        "id": account.id,
        "userId": account.user_id,
        "name": account.name,
        "maskedNumber": account.masked_number,
        "balancePaise": account.balance_paise,
        "currency": account.currency,
    }


@router.get("/account/balance")
def get_balance(session: Session = Depends(db_session), user: AuthPrincipal = Depends(principal)) -> dict:
    balance, formatted = account_service.balance(session, user.user_id)
    return {"balancePaise": balance, "formattedINR": formatted, "currency": "INR"}
