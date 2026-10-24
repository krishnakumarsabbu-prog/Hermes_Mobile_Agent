"""Transaction service: list, detail, filtering."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import NotFoundError
from app.repositories import account_repository, transaction_repository


def list_transactions(session: Session, user_id: str, params: dict) -> dict:
    account = account_repository.get_account(session, user_id)
    if account is None:
        raise NotFoundError("No account found for this user.")

    page = max(int(params.get("page", 1)), 1)
    page_size = min(max(int(params.get("pageSize", get_settings().default_page_size)), 1), get_settings().max_page_size)

    items, total = transaction_repository.list_transactions(
        session,
        account.id,
        page=page,
        page_size=page_size,
        category=params.get("category"),
        status=params.get("status"),
        start_date=params.get("startDate"),
        end_date=params.get("endDate"),
        merchant=params.get("merchant"),
        reference=params.get("reference"),
        sort=params.get("sort", "desc"),
    )

    return {
        "items": [_to_dict(t) for t in items],
        "meta": {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "totalPages": (total + page_size - 1) // page_size if page_size else 0,
        },
    }


def get_transaction(session: Session, user_id: str, transaction_id: str) -> dict:
    account = account_repository.get_account(session, user_id)
    if account is None:
        raise NotFoundError("No account found for this user.")
    txn = transaction_repository.get_transaction(session, transaction_id)
    if txn is None or txn.account_id != account.id:
        raise NotFoundError("Transaction not found.")
    return {
        **_to_dict(txn),
        "accountId": txn.account_id,
        "approvalId": txn.approval_id,
    }


def _to_dict(t) -> dict:
    return {
        "id": t.id,
        "merchant": t.merchant,
        "category": t.category,
        "amountPaise": t.amount_paise,
        "date": t.occurred_at,
        "status": t.status,
        "reference": t.reference,
        "note": t.note,
    }
