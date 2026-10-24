"""Spending service: monthly and category summaries from DB queries."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, STATUS_SUCCESSFUL
from app.repositories import account_repository
from app.services.money import month_bounds


def monthly_spending(session: Session, user_id: str, month: str | None = None) -> dict:
    account = account_repository.get_account(session, user_id)
    if account is None:
        raise ValueError("No account found for this user.")
    start_utc, end_utc, label = month_bounds(month)

    stmt = (
        select(Transaction.category, func.coalesce(func.sum(Transaction.amount_paise), 0), func.count())
        .where(
            Transaction.account_id == account.id,
            Transaction.status == STATUS_SUCCESSFUL,
            Transaction.occurred_at >= start_utc,
            Transaction.occurred_at < end_utc,
        )
        .group_by(Transaction.category)
    )
    by_category = {"Dining": 0, "Shopping": 0, "Utility": 0, "Transfer": 0}
    total = 0
    count = 0
    for category, amount, cnt in session.execute(stmt):
        by_category[category] = int(amount)
        total += int(amount)
        count += int(cnt)
    return {
        "month": label,
        "totalPaise": total,
        "byCategory": by_category,
        "transactionCount": count,
    }


def category_summary(session: Session, user_id: str, month: str | None = None) -> dict:
    summary = monthly_spending(session, user_id, month)
    total = summary["totalPaise"]
    categories = []
    for name, amount in summary["byCategory"].items():
        percentage = round((amount / total) * 100) if total else 0
        categories.append({"category": name, "amountPaise": amount, "percentage": percentage})
    return {
        "month": summary["month"],
        "totalPaise": total,
        "categories": categories,
        "transactionCount": summary["transactionCount"],
    }
