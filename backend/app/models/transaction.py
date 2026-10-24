"""Transaction model.

A transaction is an immutable record of a merchant debit or a simulated
transfer. Monetary values are integer paise. Successful transfer transactions
are linked to their approval record.
"""
from __future__ import annotations

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

CATEGORY_DINING = "Dining"
CATEGORY_SHOPPING = "Shopping"
CATEGORY_UTILITY = "Utility"
CATEGORY_TRANSFER = "Transfer"
CATEGORIES = (CATEGORY_DINING, CATEGORY_SHOPPING, CATEGORY_UTILITY, CATEGORY_TRANSFER)

STATUS_SUCCESSFUL = "successful"
STATUS_PENDING = "pending"
STATUS_CANCELLED = "cancelled"
STATUS_FAILED = "failed"
STATUSES = (STATUS_SUCCESSFUL, STATUS_PENDING, STATUS_CANCELLED, STATUS_FAILED)


class Transaction(Base):
    __tablename__ = "transactions"

    id = mapped_column(String(48), primary_key=True)
    account_id = mapped_column(String(32), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    merchant = mapped_column(String(140), nullable=False)
    category = mapped_column(String(20), nullable=False)
    amount_paise = mapped_column(BigInteger, nullable=False)
    status = mapped_column(String(16), nullable=False, server_default=STATUS_SUCCESSFUL)
    reference = mapped_column(String(48), nullable=False, unique=True)
    note = mapped_column(Text, nullable=True)
    occurred_at = mapped_column(String(40), nullable=False)
    approval_id = mapped_column(String(48), ForeignKey("transfer_approvals.id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        CheckConstraint(f"category IN {CATEGORIES}", name="ck_transactions_category"),
        CheckConstraint(f"status IN {STATUSES}", name="ck_transactions_status"),
        CheckConstraint("amount_paise > 0", name="ck_transactions_amount_positive"),
        Index("ix_transactions_account_occurred", "account_id", "occurred_at"),
        Index("ix_transactions_category", "category"),
        Index("ix_transactions_status", "status"),
    )
