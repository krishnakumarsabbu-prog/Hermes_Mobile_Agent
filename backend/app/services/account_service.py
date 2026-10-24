"""Account service — the backend is the source of truth for balances."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.account import Account
from app.repositories import account_repository, transaction_repository
from app.services.money import format_inr, month_bounds


def account_summary(session: Session, user_id: str) -> Account:
    account = account_repository.get_account(session, user_id)
    if account is None:
        raise ValueError("No account found for this user.")
    return account


def balance(session: Session, user_id: str) -> tuple[int, str]:
    account = account_summary(session, user_id)
    return account.balance_paise, format_inr(account.balance_paise)


def dashboard_summary(session: Session, user_id: str) -> dict:
    account = account_summary(session, user_id)
    start_utc, end_utc, label = month_bounds()
    from app.repositories.transaction_repository import list_transactions

    items, total = list_transactions(
        session,
        account.id,
        page=1,
        page_size=5,
        status="successful",
        start_date=start_utc,
        end_date=end_utc,
    )
    # Monthly totals via the spending service for consistency.
    from app.services.spending_service import monthly_spending

    spending = monthly_spending(session, user_id, label)
    recent = [
        {
            "id": t.id,
            "merchant": t.merchant,
            "category": t.category,
            "amountPaise": t.amount_paise,
            "date": t.occurred_at,
            "status": t.status,
            "reference": t.reference,
            "note": t.note,
        }
        for t in items
    ]
    return {
        "userId": user_id,
        "accountId": account.id,
        "balancePaise": account.balance_paise,
        "formattedBalance": format_inr(account.balance_paise),
        "currency": account.currency,
        "reportingMonth": label,
        "currentMonthExpenditurePaise": spending["totalPaise"],
        "diningExpenditurePaise": spending["byCategory"].get("Dining", 0),
        "transactionCount": spending["transactionCount"],
        "recentTransactions": recent,
    }
