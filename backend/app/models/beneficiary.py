"""Beneficiary model."""
from __future__ import annotations

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    id = mapped_column(String(40), primary_key=True)
    user_id = mapped_column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    full_name = mapped_column(String(120), nullable=False)
    alias = mapped_column(String(60), nullable=False)
    account_number_masked = mapped_column(String(30), nullable=False, server_default="••••")
    daily_limit_paise = mapped_column(BigInteger, nullable=False, server_default="10000000")

    __table_args__ = (
        CheckConstraint("daily_limit_paise >= 0", name="ck_beneficiary_daily_limit_nonnegative"),
        Index("ix_beneficiaries_user_id", "user_id"),
    )

    user: Mapped["User"] = relationship(back_populates="beneficiaries")  # noqa: F821
