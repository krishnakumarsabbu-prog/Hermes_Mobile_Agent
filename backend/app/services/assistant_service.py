"""Assistant orchestration service.

The chat flow is:

1. Resolve or create the persisted conversation (per-user isolation).
2. Append the user message.
3. Ask the real Hermes Agent Gateway (when enabled) to answer. Hermes uses
   its registered personal-banking MCP skills/tools; when it returns tool
   calls we execute them locally against the same backend tools the
   orchestrator uses, sharing the request session so every number is
   grounded in real database results and writes are atomic.
4. If Hermes is unavailable, disabled, or returns an error, fall back to the
   deterministic in-process orchestrator so the app keeps working offline.
5. Persist the assistant message and return a normalized response.

The orchestrator path (step 4) is preserved verbatim from the previous
implementation; it calls the same backend tools and never invents balances.
"""
from __future__ import annotations

import json
import re
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError, APPROVAL_ALREADY_USED, APPROVAL_EXPIRED
from app.core.logging import get_logger
from app.models.conversation import Conversation, ConversationMessage
from app.services import hermes_client
from app.services.money import format_inr, now_utc_iso
from app.services.tool_bridge import execute_tool_for_hermes
from app.tools.registry import ToolContext

# Importing these modules registers all tools.
import app.tools.account_tools  # noqa: F401
import app.tools.spending_tools  # noqa: F401
import app.tools.transaction_tools  # noqa: F401
import app.tools.beneficiary_tools  # noqa: F401
import app.tools.transfer_tools  # noqa: F401

logger = get_logger("assistant.service")


# Regex supporting currency symbols/prefixes (₹, Rs, Rs., INR), suffixes (rupees, rs, inr), or verbs (transfer/send/pay)
_AMOUNT_RE = re.compile(
    r"(?:(?:₹|rs\.?\s*|inr\s*)([0-9,]+(?:\.[0-9]+)?))|"
    r"(?:([0-9,]+(?:\.[0-9]+)?)\s*(?:rupees|rs\.?|inr)\b)|"
    r"(?:(?:transfer|send|pay)\s+(?:amount\s+of\s+)?([0-9,]+(?:\.[0-9]+)?)\b)",
    re.IGNORECASE,
)


async def handle_message(
    session: Session,
    *,
    user_id: str,
    message: str,
    conversation_id: Optional[str] = None,
    request_id: str = "",
    intent_id: Optional[str] = None,
    action: Optional[dict[str, Any]] = None,
) -> dict:
    ctx = ToolContext(session=session, user_id=user_id, request_id=request_id, intent_id=intent_id or "")
    conversation = _ensure_conversation(session, user_id, conversation_id)

    # Normalize corrupted rupee symbol (e.g. '?500' -> '₹500') caused by non-UTF8 transports/terminals
    clean_message = re.sub(r"(^|\s)\?([0-9]+(?:\.[0-9]+)?)", r"\g<1>₹\2", message)

    msg_time = now_utc_iso()
    user_msg = ConversationMessage(
        id=f"msg_{uuid.uuid4().hex[:16]}",
        conversation_id=conversation.id,
        role="user",
        text=clean_message,
        created_at=msg_time,
    )
    session.add(user_msg)
    # Commit immediately to release the SQLite write lock before calling Hermes/MCP.
    session.commit()

    settings = get_settings()
    response: dict

    # If user sent an affirmative confirmation ("yes", "confirm", etc.) without an explicit action,
    # auto-bind it to the user's active pending transfer approval.
    affirmative_words = {"yes", "confirm", "proceed", "approve", "ok", "okay", "sure", "yep", "yeah", "do it", "confirm transfer", "yes please", "please confirm", "go ahead"}
    normalized_text = clean_message.strip().lower()
    is_affirmation = normalized_text in affirmative_words or any(normalized_text.startswith(w + " ") for w in affirmative_words)

    if action is None and is_affirmation:
        from app.models.approval import TransferApproval
        pending_candidate = (
            session.query(TransferApproval)
            .filter(
                TransferApproval.user_id == user_id,
                TransferApproval.status == "WAITING_FOR_APPROVAL",
            )
            .order_by(TransferApproval.created_at.desc())
            .first()
        )
        if pending_candidate:
            action = {"type": "confirm_transfer", "approvalId": pending_candidate.id}

    if action is not None and action.get("type") == "confirm_transfer":
        approval_id = (action.get("approvalId") or "").strip()
        if not approval_id:
            raise AppError("Approval ID is required.", code="VALIDATION_ERROR", status=422)

        from app.services import transfer_service

        # Authoritative transfer authorization via existing backend transfer service
        auth_result = transfer_service.authorize(
            session,
            approval_id=approval_id,
            user_id=user_id,
            idempotency_key=f"chat-auth-{approval_id}",
            request_id=request_id,
        )
        session.commit()


        amount_str = format_inr(auth_result["approval"]["amountPaise"])
        balance_str = format_inr(auth_result["updatedBalancePaise"])
        beneficiary_name = auth_result["approval"]["beneficiary"]["fullName"]
        txn_id = auth_result["transaction"]["id"]
        ref = auth_result["transaction"]["reference"]

        authoritative_text = (
            f"Transfer of **{amount_str}** to **{beneficiary_name}** has been confirmed.\n\n"
            f"- **Status:** Completed\n"
            f"- **Transaction ID:** `{txn_id}`\n"
            f"- **Reference:** `{ref}`\n"
            f"- **Updated Balance:** **{balance_str}**"
        )

        response_text = authoritative_text
        if settings.gateway_enabled:
            try:
                hermes_confirm_prompt = (
                    f"Transfer approval {approval_id} for {amount_str} to {beneficiary_name} has been authorized and completed with transaction ID {txn_id}. "
                    "Call get_transfer_status to verify its completed status and confirm the completed transfer to the user."
                )
                hermes_res = await _hermes_response(
                    session=session,
                    ctx=ctx,
                    conversation=conversation,
                    user_message=hermes_confirm_prompt,
                    user_id=user_id,
                    request_id=request_id,
                    turn_start_time=msg_time,
                )
                h_text = hermes_res.get("text", "")
                # Authoritative safeguard: only use model text if it accurately reflects completion
                if (
                    h_text
                    and not h_text.startswith("(")
                    and "not yet" not in h_text.lower()
                    and "waiting_for_approval" not in h_text.lower()
                    and "still awaiting" not in h_text.lower()
                    and "pending" not in h_text.lower()
                ):
                    response_text = h_text
                else:
                    response_text = authoritative_text
            except Exception as exc:
                logger.warning('{"event":"hermes.confirm_error","error":"%s"}', str(exc))
                response_text = authoritative_text

        response = {
            "kind": "transfer_complete",
            "text": response_text,
            "approval": auth_result["approval"],
            "transaction": auth_result["transaction"],
        }
    elif action is not None and action.get("type") == "approve_transfer":
        response = await _handle_approval_decision(
            session=session,
            ctx=ctx,
            conversation=conversation,
            user_id=user_id,
            request_id=request_id,
            msg_time=msg_time,
            approval_id=(action.get("approvalId") or "").strip(),
            decision="approve",
            user_message=clean_message,
            settings=settings,
        )
    elif action is not None and action.get("type") == "reject_transfer":
        response = await _handle_approval_decision(
            session=session,
            ctx=ctx,
            conversation=conversation,
            user_id=user_id,
            request_id=request_id,
            msg_time=msg_time,
            approval_id=(action.get("approvalId") or "").strip(),
            decision="reject",
            user_message=clean_message,
            settings=settings,
        )
    elif settings.gateway_enabled:
        response = await _hermes_response(
            session=session,
            ctx=ctx,
            conversation=conversation,
            user_message=clean_message,
            user_id=user_id,
            request_id=request_id,
            turn_start_time=msg_time,
        )
    else:
        response = _orchestrate(ctx, clean_message)

    assistant_msg = ConversationMessage(
        id=f"msg_{uuid.uuid4().hex[:16]}",
        conversation_id=conversation.id,
        role="assistant",
        text=response["text"],
        response_json=json.dumps(response, default=str),
        created_at=now_utc_iso(),
    )
    session.add(assistant_msg)
    session.commit()

    response["conversationId"] = conversation.id
    return response


async def _handle_approval_decision(
    *,
    session: Session,
    ctx: ToolContext,
    conversation: Conversation,
    user_id: str,
    request_id: str,
    msg_time: str,
    approval_id: str,
    decision: str,
    user_message: str,
    settings: Any,
) -> dict:
    """Validate and execute an explicit approve/reject decision on a pending approval.

    The client-supplied context is never trusted for amount, beneficiary,
    ownership, or status. The authoritative approval record is fetched by
    approvalId, validated for ownership, pending state, and expiry, then the
    existing trusted transfer service performs the state transition. Hermes is
    then asked (when enabled) to continue the same conversation with the
    validated context and explicit decision so it can produce a grounded
    summary; the backend state, not the model prose, is the source of truth.
    """
    if not approval_id:
        raise AppError("Approval ID is required.", code="VALIDATION_ERROR", status=422)
    if decision not in ("approve", "reject"):
        raise AppError("Unknown approval action.", code="VALIDATION_ERROR", status=422)

    from app.models.account import Account
    from app.models.approval import TransferApproval as _Approval
    from app.models.beneficiary import Beneficiary
    from app.services import transfer_service
    from app.services.transfer_service import _approval_to_dict, _parse_iso
    from app.services.money import utc_now

    # Pre-flight authoritative validation: ownership, pending state, expiry.
    approval = (
        session.query(_Approval)
        .filter(_Approval.id == approval_id, _Approval.user_id == user_id)
        .first()
    )
    if approval is None:
        raise AppError("This approval is no longer available.", code="NOT_FOUND", status=404)
    if approval.status not in ("PREPARED", "WAITING_FOR_APPROVAL"):
        raise AppError(
            f"This approval is {approval.status.lower()} and cannot be {decision}d.",
            code=APPROVAL_ALREADY_USED,
            status=409,
        )
    if utc_now() > _parse_iso(approval.expires_at):
        from app.models.approval import APPROVAL_EXPIRED as MODEL_EXPIRED
        approval.status = MODEL_EXPIRED
        approval.decision_at = now_utc_iso()
        from app.services import audit_service as _audit
        _audit.record(session, user_id=user_id, action="transfer.expired", target=approval.id, request_id=request_id)
        session.commit()
        raise AppError("This approval has expired.", code=APPROVAL_EXPIRED, status=409)

    beneficiary = session.get(Beneficiary, approval.beneficiary_id)
    account = session.get(Account, approval.source_account_id)
    if beneficiary is None or account is None:
        raise AppError("This approval is no longer available.", code="NOT_FOUND", status=404)

    amount_str = format_inr(approval.amount_paise)
    beneficiary_name = beneficiary.full_name

    if decision == "approve":
        result = transfer_service.authorize(
            session,
            approval_id=approval_id,
            user_id=user_id,
            idempotency_key=f"chat-approve-{approval_id}",
            request_id=request_id,
        )
        session.commit()
        authoritative_text = (
            f"Transfer of **{amount_str}** to **{beneficiary_name}** has been approved and completed.\n\n"
            f"- **Status:** Completed\n"
            f"- **Transaction ID:** `{result['transaction']['id']}`\n"
            f"- **Reference:** `{result['transaction']['reference']}`\n"
            f"- **Updated Balance:** **{format_inr(result['updatedBalancePaise'])}**"
        )
        hermes_prompt = (
            f"The user explicitly approved the pending simulated transfer (approval {approval_id}) "
            f"of {amount_str} to {beneficiary_name}. The backend has authorized and completed it with "
            f"transaction ID {result['transaction']['id']}. Call get_transfer_status to verify the "
            f"completed status, then confirm the completed transfer to the user."
        )
        approval_out = result["approval"]
    else:  # reject
        cancel_result = transfer_service.cancel(
            session,
            approval_id=approval_id,
            user_id=user_id,
            request_id=request_id,
            idempotency_key=f"chat-reject-{approval_id}",
        )
        session.commit()
        authoritative_text = (
            f"Transfer of **{amount_str}** to **{beneficiary_name}** has been rejected and cancelled.\n\n"
            f"- **Status:** {cancel_result['status'].title()}\n"
            f"- No money was moved."
        )
        hermes_prompt = (
            f"The user explicitly rejected the pending simulated transfer (approval {approval_id}) "
            f"of {amount_str} to {beneficiary_name}. The backend has cancelled it. Call get_transfer_status "
            f"to verify the cancelled status, then confirm the cancellation to the user."
        )
        approval_out = cancel_result

    response_text = authoritative_text
    if settings.gateway_enabled:
        try:
            hermes_res = await _hermes_response(
                session=session,
                ctx=ctx,
                conversation=conversation,
                user_message=hermes_prompt,
                user_id=user_id,
                request_id=request_id,
                turn_start_time=msg_time,
            )
            h_text = hermes_res.get("text", "")
            lowered = (h_text or "").lower()
            if decision == "approve":
                ok = (
                    h_text
                    and not h_text.startswith("(")
                    and "not yet" not in lowered
                    and "waiting_for_approval" not in lowered
                    and "still awaiting" not in lowered
                    and "pending" not in lowered
                )
            else:
                ok = (
                    h_text
                    and not h_text.startswith("(")
                    and ("cancel" in lowered or "reject" in lowered)
                    and "completed" not in lowered
                    and "sent" not in lowered
                )
            response_text = h_text if ok else authoritative_text
        except Exception as exc:
            logger.warning('{"event":"hermes.%s_error","error":"%s"}', decision, str(exc))
            response_text = authoritative_text

    return {
        "kind": "transfer_result",
        "text": response_text,
        "approval": approval_out,
    }


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


async def _hermes_response(
    *,
    session: Session,
    ctx: ToolContext,
    conversation: Conversation,
    user_message: str,
    user_id: str,
    request_id: str,
    turn_start_time: str = "",
) -> dict:
    """Ask Hermes for a grounded answer, falling back to the orchestrator.

    Tool calls are executed in the request session via the injected executor,
    so writes share the request transaction and results are grounded. The most
    recent ``prepare_transfer`` result is captured as the approval dict; the
    model's prose is never the source of truth for transfer state.
    """
    history = _conversation_for_hermes(conversation, latest_user=user_message)
    messages = [{"role": "system", "content": hermes_client.system_prompt(user_id=user_id)}] + history

    prepared_approvals: list[dict[str, Any]] = []

    async def tool_executor(call: dict[str, Any], _call_id: str) -> dict[str, Any]:
        result = execute_tool_for_hermes(
            tool_name=call["name"],
            args=call.get("args") or {},
            user_id=user_id,
            request_id=request_id,
            session=session,
        )
        if call["name"] == "prepare_transfer":
            prepared_approvals.append(result)
        return result

    try:
        result = await hermes_client.chat(
            messages=messages,
            conversation_id=conversation.id,
            request_id=request_id,
            user_id=user_id,
            tool_executor=tool_executor,
        )
    except hermes_client.HermesError as exc:
        logger.warning('{"event":"hermes.fallback","requestId":"%s","code":"%s"}', request_id, exc.code)
        response = _orchestrate(ctx, user_message)
        response["text"] = (
            f"{response['text']}\n\n(I reached this using the offline assistant because {exc.message.lower()})"
        )
        return response

    text = (result.content or "").strip()
    if not text:
        response = _orchestrate(ctx, user_message)
        response["text"] = (
            f"{response['text']}\n\n(The assistant returned tool results without a summary; "
            "showing the grounded offline view.)"
        )
        return response

    approval = prepared_approvals[-1] if prepared_approvals else None
    if not approval:
        from app.models.account import Account
        from app.models.approval import TransferApproval
        from app.models.beneficiary import Beneficiary
        from app.services.transfer_service import _approval_to_dict

        # 1. Search for approval ID directly in model prose (e.g. "Approval ID: appr_242212d8f6864e599707")
        appr_id_match = re.search(r"\b(appr_[a-fA-F0-9]+)\b", text)
        if appr_id_match:
            candidate = session.get(TransferApproval, appr_id_match.group(1))
            if candidate and candidate.user_id == user_id:
                account = session.get(Account, candidate.source_account_id)
                beneficiary = session.get(Beneficiary, candidate.beneficiary_id)
                if account and beneficiary:
                    approval = _approval_to_dict(candidate, beneficiary, account.balance_paise)

        # 2. Check if prose indicates WAITING_FOR_APPROVAL or transfer preview
        if not approval and any(term in text.lower() for term in ("waiting_for_approval", "pending your confirmation", "pending approval", "transfer prepared")):
            recent_approval = (
                session.query(TransferApproval)
                .filter(
                    TransferApproval.user_id == user_id,
                    TransferApproval.status == "WAITING_FOR_APPROVAL",
                )
                .order_by(TransferApproval.created_at.desc())
                .first()
            )
            if recent_approval:
                account = session.get(Account, recent_approval.source_account_id)
                beneficiary = session.get(Beneficiary, recent_approval.beneficiary_id)
                if account and beneficiary:
                    approval = _approval_to_dict(recent_approval, beneficiary, account.balance_paise)

        # 3. Check for recently created approval since turn_start_time
        if not approval and turn_start_time:
            recent_approval = (
                session.query(TransferApproval)
                .filter(
                    TransferApproval.user_id == user_id,
                    TransferApproval.status == "WAITING_FOR_APPROVAL",
                    TransferApproval.created_at >= turn_start_time,
                )
                .order_by(TransferApproval.created_at.desc())
                .first()
            )
            if recent_approval:
                account = session.get(Account, recent_approval.source_account_id)
                beneficiary = session.get(Beneficiary, recent_approval.beneficiary_id)
                if account and beneficiary:
                    approval = _approval_to_dict(recent_approval, beneficiary, account.balance_paise)


    if approval:
        status_val = approval.get("status")
        # Authoritative guard: ensure model prose cannot claim completion while backend approval is still pending
        if status_val in ("WAITING_FOR_APPROVAL", "PREPARED"):
            lowered = text.lower()
            if any(term in lowered for term in ("has been sent", "transferred", "completed", "complete", "money sent", "debited")):
                if not any(term in lowered for term in ("pending", "approval", "confirm", "preview")):
                    text = (
                        f"Transfer preview prepared for **{format_inr(approval['amountPaise'])}** to "
                        f"**{approval['beneficiary']['fullName']}**.\n\n"
                        "⚠️ This is a pending approval only — no money has been moved yet. "
                        "Please confirm to proceed."
                    )

    return {
        "kind": "transfer_approval" if approval else "normal",
        "text": text,
        "approval": approval,
    }


def _conversation_for_hermes(conversation: Conversation, *, latest_user: str) -> list[dict]:
    """Build user/assistant message history for Hermes from the conversation.

    Tool messages and raw tool output are dropped to avoid leaking internal
    payloads and to keep the history compact.
    """
    history: list[dict] = []
    for m in sorted(conversation.messages, key=lambda x: x.created_at):
        if m.role == "user":
            history.append({"role": "user", "content": m.text})
        elif m.role == "assistant":
            history.append({"role": "assistant", "content": m.text})
    if not history:
        history.append({"role": "user", "content": latest_user})
    elif history[-1].get("content") != latest_user:
        if history[-1].get("role") == "user":
            history[-1]["content"] = f"{history[-1]['content']}\n\n{latest_user}"
        else:
            history.append({"role": "user", "content": latest_user})
    return history



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

    if ("spending" in normalized or "spent" in normalized) and "transfer" in normalized:
        return _composite_spending_and_transfer(ctx, message, normalized)

    if "transfer" in normalized:
        return _transfer_intent(ctx, message, normalized)

    if "dining" in normalized:
        spending = _run(ctx, "get_monthly_spending", {})
        dining = spending["byCategory"].get("Dining", 0)
        return {"kind": "analysis", "text": f"You spent {format_inr(dining)} on dining this month."}

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


def _resolve_proposal_idempotency_key(ctx: ToolContext) -> str:
    if ctx.intent_id:
        return ctx.intent_id if ctx.intent_id.startswith("agent-intent-") else f"agent-intent-{ctx.intent_id}"
    if ctx.request_id:
        return f"agent-intent-{ctx.request_id}"
    return f"agent-intent-{uuid.uuid4().hex}"


def _composite_spending_and_transfer(ctx: ToolContext, raw: str, normalized: str) -> dict:
    spending = _run(ctx, "get_monthly_spending", {})
    dining = spending["byCategory"].get("Dining", 0)
    balance_info = _run(ctx, "get_balance", {})
    balance = balance_info["balancePaise"]

    amount_paise = _extract_amount(raw, normalized)
    if amount_paise is None:
        name = _extract_beneficiary_name(normalized)
        target = f" to {name.title()}" if name else ""
        return {
            "kind": "clarification",
            "text": (
                f"Here is your monthly snapshot: you have spent {format_inr(spending['totalPaise'])} this month, "
                f"including {format_inr(dining)} on dining. Your current balance is {format_inr(balance)}. "
                f"How much would you like to transfer{target}?"
            ),
        }

    name = _extract_beneficiary_name(normalized)
    try:
        beneficiary = _run(ctx, "resolve_beneficiary", {"name": name})
    except AppError as exc:
        return {"kind": "error", "text": exc.message}

    idempotency_key = _resolve_proposal_idempotency_key(ctx)
    try:
        approval = _run(
            ctx,
            "prepare_transfer",
            {"beneficiaryId": beneficiary["id"], "amountPaise": amount_paise, "idempotencyKey": idempotency_key},
        )
    except AppError as exc:
        return {"kind": "error", "text": _affordability_text(spending, dining, balance, amount_paise, exc.message)}

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
    amount_paise = _extract_amount(raw, normalized)
    if amount_paise is None:
        name = _extract_beneficiary_name(normalized)
        target = f" to {name.title()}" if name else ""
        return {"kind": "clarification", "text": f"How much would you like to transfer{target}?"}

    name = _extract_beneficiary_name(normalized)
    try:
        beneficiary = _run(ctx, "resolve_beneficiary", {"name": name})
    except AppError as exc:
        return {"kind": "error", "text": exc.message}

    idempotency_key = _resolve_proposal_idempotency_key(ctx)
    try:
        approval = _run(
            ctx,
            "prepare_transfer",
            {"beneficiaryId": beneficiary["id"], "amountPaise": amount_paise, "idempotencyKey": idempotency_key},
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


def _extract_amount(raw: str, normalized: str) -> int | None:
    match = _AMOUNT_RE.search(raw)
    if not match:
        match = _AMOUNT_RE.search(normalized)
    if not match:
        return None

    val_str = match.group(1) or match.group(2) or (match.group(3) if len(match.groups()) >= 3 else None)
    if not val_str:
        return None

    cleaned = val_str.replace(",", "").strip()
    try:
        d = Decimal(cleaned)
    except InvalidOperation:
        return None

    if d <= 0:
        return None
    if d.as_tuple().exponent < -2:
        return None

    paise = int(round(d * 100))
    if paise <= 0:
        return None
    return paise


def _extract_beneficiary_name(normalized: str) -> str:
    match = re.search(r"\bto\s+([a-z]+)", normalized)
    if match:
        return match.group(1)
    return "ravi"
