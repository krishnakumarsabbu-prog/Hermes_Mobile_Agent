"""Assistant orchestration service.

Phase 2 uses a deterministic, rule-based orchestrator that calls registered
backend tools and real database results. It never invents balances or spending
amounts. The interface is designed so a real Hermes runtime can implement it
later.
"""
from __future__ import annotations

import json
import re
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.conversation import Conversation, ConversationMessage
from app.services.money import format_inr, now_utc_iso
from app.tools.registry import ToolContext

# Importing these modules registers all tools.
import app.tools.account_tools  # noqa: F401
import app.tools.spending_tools  # noqa: F401
import app.tools.transaction_tools  # noqa: F401
import app.tools.beneficiary_tools  # noqa: F401
import app.tools.transfer_tools  # noqa: F401


_AMOUNT_RE = re.compile(r"(?:₹|rs\.?\s?|inr\s?)([\d,]+)", re.IGNORECASE)


def handle_message(session: Session, *, user_id: str, message: str, conversation_id: Optional[str] = None, request_id: str = "") -> dict:
    ctx = ToolContext(session=session, user_id=user_id, request_id=request_id)
    conversation = _ensure_conversation(session, user_id, conversation_id)

    user_msg = ConversationMessage(
        id=f"msg_{uuid.uuid4().hex[:16]}",
        conversation_id=conversation.id,
        role="user",
        text=message,
        created_at=now_utc_iso(),
    )
    session.add(user_msg)
    session.flush()

    response = _orchestrate(ctx, message)

    assistant_msg = ConversationMessage(
        id=f"msg_{uuid.uuid4().hex[:16]}",
        conversation_id=conversation.id,
        role="assistant",
        text=response["text"],
        response_json=json.dumps(response, default=str),
        created_at=now_utc_iso(),
    )
    session.add(assistant_msg)
    session.flush()
    session.commit()

    response["conversationId"] = conversation.id
    return response


def get_conversation(session: Session, *, user_id: str, conversation_id: str) -> dict:
    conv = session.get(Conversation, conversation_id)
    if conv is None or conv.user_id != user_id:
        from app.core.errors import NotFoundError

        raise NotFoundError("Conversation not found.")
    return {
        "id": conv.id,
        "userId": conv.user_id,
        "title": conv.title,
        "createdAt": conv.created_at,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "text": m.text,
                "response": json.loads(m.response_json) if m.response_json else None,
                "createdAt": m.created_at,
            }
            for m in sorted(conv.messages, key=lambda x: x.created_at)
        ],
    }


def _ensure_conversation(session: Session, user_id: str, conversation_id: Optional[str]) -> Conversation:
    if conversation_id:
        conv = session.get(Conversation, conversation_id)
        if conv is None or conv.user_id != user_id:
            from app.core.errors import NotFoundError

            raise NotFoundError("Conversation not found.")
        return conv
    conv = Conversation(
        id=f"conv_{uuid.uuid4().hex[:16]}",
        user_id=user_id,
        title="Conversation",
        created_at=now_utc_iso(),
    )
    session.add(conv)
    session.flush()
    return conv


def _orchestrate(ctx: ToolContext, message: str) -> dict:
    normalized = message.lower()

    # Composite intent: spending + dining + conditional transfer to <name>.
    if ("spending" in normalized or "spent" in normalized) and "transfer" in normalized:
        return _composite_spending_and_transfer(ctx, message, normalized)

    if "transfer" in normalized:
        return _transfer_intent(ctx, message, normalized)

    if "dining" in normalized:
        spending = _run(ctx, "get_monthly_spending", {})
        dining = spending["byCategory"].get("Dining", 0)
        return {
            "kind": "analysis",
            "text": f"You spent {format_inr(dining)} on dining this month.",
        }

    if "spending" in normalized or "month" in normalized or "spent" in normalized:
        spending = _run(ctx, "get_monthly_spending", {})
        return {
            "kind": "analysis",
            "text": f"You have spent {format_inr(spending['totalPaise'])} this month across {spending['transactionCount']} transactions.",
        }

    if "recent" in normalized or "transaction" in normalized or "history" in normalized:
        result = _run(ctx, "list_transactions", {"pageSize": 5})
        count = result["meta"]["total"]
        return {
            "kind": "history",
            "text": f"You have {count} transactions on file. I can show the full activity list from the Activity tab.",
        }

    return {
        "kind": "normal",
        "text": "I can help with spending insights, recent transactions, or a simulated transfer to Ravi.",
    }


def _composite_spending_and_transfer(ctx: ToolContext, raw: str, normalized: str) -> dict:
    """Handle the canonical prompt:

    'Show me my spending for this month, tell me how much I spent on dining,
    and transfer ₹75,000 to Ravi if I can afford it.'
    """
    spending = _run(ctx, "get_monthly_spending", {})
    dining = spending["byCategory"].get("Dining", 0)
    balance_info = _run(ctx, "get_balance", {})
    balance = balance_info["balancePaise"]

    name = _extract_beneficiary_name(normalized)
    amount_paise = _extract_amount(raw, normalized)

    try:
        beneficiary = _run(ctx, "resolve_beneficiary", {"name": name})
    except AppError as exc:
        return {"kind": "error", "text": exc.message}

    # Affordability + limit check happens inside prepare_transfer.
    try:
        approval = _run(
            ctx,
            "prepare_transfer",
            {
                "beneficiaryId": beneficiary["id"],
                "amountPaise": amount_paise,
                "idempotencyKey": f"agent-{ctx.user_id}-{amount_paise}-{beneficiary['id']}",
            },
        )
    except AppError as exc:
        return {
            "kind": "error",
            "text": _affordability_text(spending, dining, balance, amount_paise, exc.message),
        }

    summary = {
        "spendingPaise": spending["totalPaise"],
        "diningPaise": dining,
        "balancePaise": approval["currentBalancePaise"],
        "proposedTransferPaise": approval["amountPaise"],
        "projectedBalancePaise": approval["projectedBalancePaise"],
    }
    text = (
        f"Here is your monthly snapshot: you have spent {format_inr(spending['totalPaise'])} this month, "
        f"including {format_inr(dining)} on dining. Your current balance is {format_inr(approval['currentBalancePaise'])}. "
        f"I can prepare a simulated transfer of {format_inr(approval['amountPaise'])} to {beneficiary['fullName']}, "
        f"leaving {format_inr(approval['projectedBalancePaise'])}. Please review and explicitly authorize it below."
    )
    return {"kind": "transfer_approval", "approval": approval, "summary": summary, "text": text}


def _affordability_text(spending: dict, dining: int, balance: int, amount_paise: int, reason: str) -> str:
    return (
        f"Here is your monthly snapshot: you have spent {format_inr(spending['totalPaise'])} this month, "
        f"including {format_inr(dining)} on dining. Your current balance is {format_inr(balance)}. "
        f"I could not prepare the {format_inr(amount_paise)} transfer: {reason}"
    )


def _transfer_intent(ctx: ToolContext, raw: str, normalized: str) -> dict:
    name = _extract_beneficiary_name(normalized)
    amount_paise = _extract_amount(raw, normalized)
    try:
        beneficiary = _run(ctx, "resolve_beneficiary", {"name": name})
    except AppError as exc:
        return {"kind": "error", "text": exc.message}
    try:
        approval = _run(
            ctx,
            "prepare_transfer",
            {
                "beneficiaryId": beneficiary["id"],
                "amountPaise": amount_paise,
                "idempotencyKey": f"agent-{ctx.user_id}-{amount_paise}-{beneficiary['id']}",
            },
        )
    except AppError as exc:
        return {"kind": "error", "text": exc.message}
    text = (
        f"I have prepared a simulated transfer of {format_inr(approval['amountPaise'])} to {beneficiary['fullName']}, "
        f"leaving {format_inr(approval['projectedBalancePaise'])}. Please review and explicitly authorize it below."
    )
    return {"kind": "transfer_approval", "approval": approval, "text": text}


def _run(ctx: ToolContext, tool_name: str, args: dict) -> dict:
    from app.tools.registry import run_tool

    return run_tool(tool_name, ctx, args)


def _extract_amount(raw: str, normalized: str) -> int:
    match = _AMOUNT_RE.search(raw)
    if match:
        rupees = int(match.group(1).replace(",", ""))
        return rupees * 100
    return 7500000  # default ₹75,000 for the canonical prompt


def _extract_beneficiary_name(normalized: str) -> str:
    # Simple keyword extraction: "to <name>".
    match = re.search(r"\bto\s+([a-z]+)", normalized)
    if match:
        return match.group(1)
    return "ravi"
