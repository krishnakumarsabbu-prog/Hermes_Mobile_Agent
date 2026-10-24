"""Beneficiary service with user-scoped access."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.repositories import beneficiary_repository


def list_beneficiaries(session: Session, user_id: str, params: dict) -> dict:
    page = max(int(params.get("page", 1)), 1)
    page_size = min(max(int(params.get("pageSize", 20)), 1), 100)
    search = params.get("search")
    items, total = beneficiary_repository.list_beneficiaries(
        session, user_id, search=search, page=page, page_size=page_size
    )
    return {
        "items": [_to_dict(b) for b in items],
        "meta": {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "totalPages": (total + page_size - 1) // page_size if page_size else 0,
        },
    }


def get_beneficiary(session: Session, user_id: str, beneficiary_id: str) -> dict:
    ben = beneficiary_repository.get_beneficiary(session, user_id, beneficiary_id)
    if ben is None:
        raise NotFoundError("Beneficiary not found.")
    return _to_dict(ben)


def _to_dict(b) -> dict:
    return {
        "id": b.id,
        "fullName": b.full_name,
        "alias": b.alias,
        "dailyLimitPaise": b.daily_limit_paise,
    }
