"""Account repository."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account, User


def get_user(session: Session, user_id: str) -> User | None:
    return session.get(User, user_id)


def get_account(session: Session, user_id: str) -> Account | None:
    stmt = select(Account).where(Account.user_id == user_id).order_by(Account.id).limit(1)
    return session.scalars(stmt).first()


def get_account_by_id(session: Session, account_id: str) -> Account | None:
    return session.get(Account, account_id)


def list_accounts(session: Session, user_id: str) -> list[Account]:
    stmt = select(Account).where(Account.user_id == user_id).order_by(Account.id)
    return list(session.scalars(stmt))
