"""Ledger entries — immutable debit/credit records tied to a transfer.

Ledger rows are insert-only. Every successful transfer produces exactly one
debit against the source account. Account balances reconcile with the sum of
ledger entries plus the opening balance.
"""
from __future__ import annotations

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

ENTRY_DEBIT = "DEBIT"
ENTRY_CREDIT = "CREDIT"
ENTRY_TYPES = (ENTRY_DEBIT, ENTRY_CREDIT)


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = mapped_column(String(48), primary_key=True)
    account_id = mapped_column(String(32), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    approval_id = mapped_column(String(48), ForeignKey("transfer_approvals.id", ondelete="CASCADE"), nullable=True)
    transaction_id = mapped_column(String(48), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=True)
    entry_type = mapped_column(String(8), nullable=False)
    amount_paise = mapped_column(BigInteger, nullable=False)
    reference = mapped_column(String(48), nullable=False)
    created_at = mapped_column(String(40), nullable=False)

    __table_args__ = (
        CheckConstraint(f"entry_type IN {ENTRY_TYPES}", name="ck_ledger_entry_type"),
        CheckConstraint("amount_paise > 0", name="ck_ledger_amount_positive"),
        Index("ix_ledger_account", "account_id"),
        Index("ix_ledger_approval", "approval_id"),
    )
