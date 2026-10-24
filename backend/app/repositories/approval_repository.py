"""Transfer approval repository."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.approval import TransferApproval


def get_approval(session: Session, approval_id: str) -> TransferApproval | None:
    return session.get(TransferApproval, approval_id)


def get_approval_for_user(session: Session, approval_id: str, user_id: str) -> TransferApproval | None:
    obj = session.get(TransferApproval, approval_id)
    if obj is None or obj.user_id != user_id:
        return None
    return obj
