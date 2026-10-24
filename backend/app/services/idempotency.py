"""Idempotency helpers shared by transfer endpoints."""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, IDEMPOTENCY_CONFLICT
from app.models.audit import IdempotencyRecord
from app.services.money import now_utc_iso


def payload_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def lookup(session: Session, key: str, user_id: str) -> IdempotencyRecord | None:
    stmt = select(IdempotencyRecord).where(
        IdempotencyRecord.key == key,
        IdempotencyRecord.user_id == user_id,
    )
    return session.scalars(stmt).first()


def save(session: Session, *, key: str, user_id: str, endpoint: str, payload: dict, status_code: int, response: dict) -> IdempotencyRecord:
    record = IdempotencyRecord(
        id=f"idem_{uuid.uuid4().hex[:20]}",
        key=key,
        user_id=user_id,
        endpoint=endpoint,
        payload_hash=payload_hash(payload),
        status_code=str(status_code),
        response_json=json.dumps(response, default=str),
        created_at=now_utc_iso(),
    )
    session.add(record)
    return record


def check_conflict(existing: IdempotencyRecord, payload: dict) -> None:
    if existing.payload_hash != payload_hash(payload):
        raise ConflictError(
            "This idempotency key was used with a different request body.",
            code=IDEMPOTENCY_CONFLICT,
        )
