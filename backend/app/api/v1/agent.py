"""Assistant endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session, principal, request_id_dep
from app.core.security import AuthPrincipal
from app.schemas.assistant import ChatRequest
from app.services import assistant_service

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.post("/chat")
def chat(
    body: ChatRequest,
    session: Session = Depends(db_session),
    user: AuthPrincipal = Depends(principal),
    request_id: str = Depends(request_id_dep),
) -> dict:
    return assistant_service.handle_message(
        session, user_id=user.user_id, message=body.message, conversation_id=body.conversationId, request_id=request_id
    )


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    session: Session = Depends(db_session),
    user: AuthPrincipal = Depends(principal),
) -> dict:
    return assistant_service.get_conversation(session, user_id=user.user_id, conversation_id=conversation_id)
