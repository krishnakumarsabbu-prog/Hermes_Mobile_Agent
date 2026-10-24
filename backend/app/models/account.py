"""User and account models."""
from __future__ import annotations

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = mapped_column(String(32), primary_key=True)
    display_name = mapped_column(String(120), nullable=False)
    profile = mapped_column(String(60), nullable=False, server_default="default")

    accounts: Mapped[list["Account"]] = relationship(back_populates="user")  # noqa: F821
    beneficiaries: Mapped[list["Beneficiary"]] = relationship(back_populates="user")  # noqa: F821


class Account(Base):
    __tablename__ = "accounts"

    id = mapped_column(String(32), primary_key=True)
    user_id = mapped_column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = mapped_column(String(80), nullable=False)
    masked_number = mapped_column(String(20), nullable=False)
    currency = mapped_column(String(3), nullable=False, server_default="INR")
    # All monetary values are integer paise.
    balance_paise = mapped_column(BigInteger, nullable=False, server_default="0")
    opening_balance_paise = mapped_column(BigInteger, nullable=False, server_default="0")

    __table_args__ = (
        CheckConstraint("balance_paise >= 0", name="ck_accounts_balance_nonnegative"),
        Index("ix_accounts_user_id", "user_id"),
    )

    user: Mapped[User] = relationship(back_populates="accounts")
