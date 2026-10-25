"""Assistant endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session, principal, request_id_dep
from app.core.security import AuthPrincipal
from app.schemas.assistant import ChatRequest
from app.services import assistant_service

import json

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.post("/chat")
async def chat(
    body: ChatRequest,
    session: Session = Depends(db_session),
    user: AuthPrincipal = Depends(principal),
    request_id: str = Depends(request_id_dep),
) -> dict:
    print("\n" + "=" * 60)
    print(">>> [INCOMING /api/v1/agent/chat REQUEST JSON]")
    print(f"User ID:    {user.user_id}")
    print(f"Request ID: {request_id}")
    print(f"Payload:\n{json.dumps(body.model_dump(), indent=2, ensure_ascii=False)}")
    print("=" * 60 + "\n")

    result = await assistant_service.handle_message(
        session,
        user_id=user.user_id,
        message=body.message,
        conversation_id=body.conversationId,
        request_id=request_id,
        intent_id=body.intentId,
        action=body.action.model_dump() if body.action else None,
    )

    print("\n" + "=" * 60)
    print("<<< [OUTGOING /api/v1/agent/chat RESPONSE JSON]")
    print(f"Response:\n{json.dumps(result, default=str, indent=2, ensure_ascii=False)}")
    print("=" * 60 + "\n")

    return result


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    session: Session = Depends(db_session),
    user: AuthPrincipal = Depends(principal),
) -> dict:
    return assistant_service.get_conversation(session, user_id=user.user_id, conversation_id=conversation_id)
