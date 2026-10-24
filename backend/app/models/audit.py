"""Audit events and idempotency records."""
from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = mapped_column(String(48), primary_key=True)
    user_id = mapped_column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = mapped_column(String(60), nullable=False)
    target = mapped_column(String(60), nullable=True)
    detail = mapped_column(Text, nullable=True)
    request_id = mapped_column(String(64), nullable=True)
    created_at = mapped_column(String(40), nullable=False)

    __table_args__ = (Index("ix_audit_user_action", "user_id", "action"),)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = mapped_column(String(48), primary_key=True)
    key = mapped_column(String(120), nullable=False)
    user_id = mapped_column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    endpoint = mapped_column(String(80), nullable=False)
    payload_hash = mapped_column(String(128), nullable=False)
    status_code = mapped_column(String(8), nullable=False)
    response_json = mapped_column(Text, nullable=True)
    created_at = mapped_column(String(40), nullable=False)

    __table_args__ = (
        Index("ix_idem_key_user", "key", "user_id"),
        UniqueConstraint("key", "user_id", name="uq_idem_key_user"),
    )
