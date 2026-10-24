"""Beneficiary repository."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.beneficiary import Beneficiary


def get_beneficiary(session: Session, user_id: str, beneficiary_id: str) -> Beneficiary | None:
    stmt = select(Beneficiary).where(
        Beneficiary.user_id == user_id,
        Beneficiary.id == beneficiary_id,
    )
    return session.scalars(stmt).first()


def list_beneficiaries(
    session: Session,
    user_id: str,
    *,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Beneficiary], int]:
    stmt = select(Beneficiary).where(Beneficiary.user_id == user_id)
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Beneficiary.full_name).like(like),
                func.lower(Beneficiary.alias).like(like),
            )
        )
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = int(session.scalar(count_stmt) or 0)
    stmt = stmt.order_by(Beneficiary.full_name).offset((page - 1) * page_size).limit(page_size)
    return list(session.scalars(stmt)), total


def find_beneficiary_by_name(session: Session, user_id: str, name: str) -> list[Beneficiary]:
    """Resolve a free-text beneficiary name. Matches alias or full_name."""
    like = f"%{name.lower()}%"
    stmt = select(Beneficiary).where(
        Beneficiary.user_id == user_id,
        or_(
            func.lower(Beneficiary.alias).like(like),
            func.lower(Beneficiary.full_name).like(like),
        ),
    )
    return list(session.scalars(stmt))
