"""Audit service — append-only audit events."""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.audit import AuditEvent
from app.services.money import now_utc_iso


def record(session: Session, *, user_id: str, action: str, target: str | None = None, detail: str | None = None, request_id: str | None = None) -> None:
    event = AuditEvent(
        id=f"aud_{uuid.uuid4().hex[:20]}",
        user_id=user_id,
        action=action,
        target=target,
        detail=detail,
        request_id=request_id,
        created_at=now_utc_iso(),
    )
    session.add(event)
