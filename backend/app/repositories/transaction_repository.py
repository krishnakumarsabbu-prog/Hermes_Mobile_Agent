"""Transaction repository with filtering and pagination."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


def list_transactions(
    session: Session,
    account_id: str,
    *,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    merchant: Optional[str] = None,
    reference: Optional[str] = None,
    sort: str = "desc",
) -> tuple[list[Transaction], int]:
    stmt = select(Transaction).where(Transaction.account_id == account_id)

    if category:
        stmt = stmt.where(Transaction.category == category)
    if status:
        stmt = stmt.where(Transaction.status == status)
    if start_date:
        stmt = stmt.where(Transaction.occurred_at >= start_date)
    if end_date:
        stmt = stmt.where(Transaction.occurred_at <= end_date)
    if merchant:
        stmt = stmt.where(Transaction.merchant.ilike(f"%{merchant}%"))
    if reference:
        stmt = stmt.where(Transaction.reference.ilike(f"%{reference}%"))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = int(session.scalar(count_stmt) or 0)

    stmt = stmt.order_by(Transaction.occurred_at.desc() if sort != "asc" else Transaction.occurred_at.asc())
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    items = list(session.scalars(stmt))
    return items, total


def get_transaction(session: Session, transaction_id: str) -> Transaction | None:
    return session.get(Transaction, transaction_id)


def successful_amount_sum(session: Session, account_id: str) -> int:
    stmt = select(func.coalesce(func.sum(Transaction.amount_paise), 0)).where(
        Transaction.account_id == account_id,
        Transaction.status == "successful",
    )
    return int(session.scalar(stmt) or 0)
