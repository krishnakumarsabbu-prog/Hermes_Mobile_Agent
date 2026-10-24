"""Transfer approval model.

The approval binds the exact transfer details (beneficiary, amount, source
account) and carries an optimistic concurrency version so two concurrent
authorizations cannot both succeed. The client cannot change the beneficiary
or amount after preparation.
"""
from __future__ import annotations

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

APPROVAL_PREPARED = "PREPARED"
APPROVAL_WAITING = "WAITING_FOR_APPROVAL"
APPROVAL_COMPLETED = "COMPLETED"
APPROVAL_CANCELLED = "CANCELLED"
APPROVAL_REJECTED = "REJECTED"
APPROVAL_EXPIRED = "EXPIRED"
APPROVAL_FAILED = "FAILED"
APPROVAL_STATES = (
    APPROVAL_PREPARED,
    APPROVAL_WAITING,
    APPROVAL_COMPLETED,
    APPROVAL_CANCELLED,
    APPROVAL_REJECTED,
    APPROVAL_EXPIRED,
    APPROVAL_FAILED,
)
PENDING_STATES = (APPROVAL_PREPARED, APPROVAL_WAITING)


class TransferApproval(Base):
    __tablename__ = "transfer_approvals"

    id = mapped_column(String(48), primary_key=True)
    user_id = mapped_column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_account_id = mapped_column(String(32), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    beneficiary_id = mapped_column(String(40), ForeignKey("beneficiaries.id", ondelete="CASCADE"), nullable=False)
    amount_paise = mapped_column(BigInteger, nullable=False)
    currency = mapped_column(String(3), nullable=False, server_default="INR")
    status = mapped_column(String(24), nullable=False, server_default=APPROVAL_WAITING)
    created_at = mapped_column(String(40), nullable=False)
    expires_at = mapped_column(String(40), nullable=False)
    decision_at = mapped_column(String(40), nullable=True)
    idempotency_key = mapped_column(String(120), nullable=False)
    transaction_id = mapped_column(String(48), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)
    version = mapped_column(BigInteger, nullable=False, server_default="1")

    __table_args__ = (
        CheckConstraint(f"status IN {APPROVAL_STATES}", name="ck_approval_status"),
        CheckConstraint("amount_paise > 0", name="ck_approval_amount_positive"),
        Index("ix_approval_user_status", "user_id", "status"),
        Index("ix_approval_idem", "idempotency_key"),
        UniqueConstraint("idempotency_key", "user_id", name="uq_approval_idem_user"),
    )
