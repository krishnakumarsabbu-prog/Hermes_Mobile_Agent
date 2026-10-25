"""Bridge between Hermes MCP tool names and the backend tool registry.

Hermes calls MCP tools by their registered MCP names
(``get_account_balance``, ``list_beneficiaries``, ``prepare_transfer`` etc.).
Several of those names differ from the in-process registry names
(``get_balance``, ``resolve_beneficiary``), and a few MCP tools map to more
than one backend tool. This module normalises the names and args so the same
grounded backend logic serves both code paths.

Tool execution can run inside a caller-supplied session (so it shares the
request's transaction and avoids nested-write deadlocks on SQLite) or in a
short-lived scoped session when none is supplied. Results are the structured
dicts the backend tools already produce; we never fabricate data.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.database import session_scope
from app.core.errors import AppError
from app.services.money import format_inr
from app.tools.registry import ToolContext, run_tool

# Importing these modules registers all backend tools with the registry.
import app.tools.account_tools  # noqa: F401
import app.tools.beneficiary_tools  # noqa: F401
import app.tools.spending_tools  # noqa: F401
import app.tools.transaction_tools  # noqa: F401
import app.tools.transfer_tools  # noqa: F401


def execute_tool_for_hermes(
    *,
    tool_name: str,
    args: dict[str, Any],
    user_id: str,
    request_id: str = "",
    session: Optional[Session] = None,
) -> dict[str, Any]:
    """Run a Hermes-named tool against the real backend and return its dict.

    When ``session`` is supplied, execution shares that session/transaction
    (used by the assistant service so tool writes and the conversation
    persist atomically). Otherwise a short-lived scoped session is used.
    Raises ``ValueError`` for unknown tools and propagates ``AppError``.
    """
    handler = _HANDLERS.get(tool_name)
    if handler is None:
        raise ValueError(f"Unknown banking tool: {tool_name}")

    if session is not None:
        ctx = ToolContext(session=session, user_id=user_id, request_id=request_id)
        return handler(ctx, args)

    with session_scope() as own_session:
        ctx = ToolContext(session=own_session, user_id=user_id, request_id=request_id)
        return handler(ctx, args)


def _get_account_balance(ctx: ToolContext, _args: dict[str, Any]) -> dict[str, Any]:
    result = run_tool("get_balance", ctx, {})
    return {
        "balancePaise": result["balancePaise"],
        "accountId": result["accountId"],
        "formatted": format_inr(result["balancePaise"]),
        "currency": "INR",
    }


def _get_account_summary(ctx: ToolContext, _args: dict[str, Any]) -> dict[str, Any]:
    return run_tool("get_account_summary", ctx, {})


def _list_transactions(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    return run_tool("list_transactions", ctx, _pick(args, {"pageSize", "page", "category"}))


def _get_transaction_details(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    from app.services import transaction_service

    tx_id = (args.get("transactionId") or args.get("id") or "").strip()
    if not tx_id:
        raise AppError("A transaction id is required.", code="VALIDATION_ERROR", status=422)
    return transaction_service.get_transaction(ctx.session, ctx.user_id, tx_id)


def _get_transfer_status(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    from app.services import transfer_service

    approval_id = (args.get("approvalId") or args.get("id") or "").strip()
    if not approval_id:
        raise AppError("An approval id is required.", code="VALIDATION_ERROR", status=422)
    return transfer_service.status(ctx.session, approval_id=approval_id, user_id=ctx.user_id)


def _get_monthly_spending(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    return run_tool("get_monthly_spending", ctx, _pick(args, {"month"}))


def _get_category_spending(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    return run_tool("get_category_spending", ctx, _pick(args, {"month"}))


def _list_beneficiaries(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    from app.repositories import beneficiary_repository

    search = (args.get("search") or "").strip() or None
    page = max(1, int(args.get("page") or 1))
    page_size = max(1, min(100, int(args.get("pageSize") or 20)))
    matches, total = beneficiary_repository.list_beneficiaries(
        ctx.session, ctx.user_id, search=search, page=page, page_size=page_size
    )
    page_items = [
        {"id": b.id, "fullName": b.full_name, "alias": b.alias, "dailyLimitPaise": b.daily_limit_paise}
        for b in matches
    ]
    return {
        "items": page_items,
        "meta": {"page": page, "pageSize": page_size, "total": total},
    }


def _prepare_transfer(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    beneficiary_id = (args.get("beneficiaryId") or "").strip()
    amount = args.get("amountPaise")
    currency = (args.get("currency") or "INR").strip() or "INR"
    idem = (args.get("idempotencyKey") or "").strip()
    if not beneficiary_id:
        raise AppError("A beneficiary id is required.", code="VALIDATION_ERROR", status=422)
    if amount is None:
        raise AppError("A transfer amount is required.", code="VALIDATION_ERROR", status=422)
    if not idem:
        raise AppError("An idempotency key is required.", code="VALIDATION_ERROR", status=422)
    return run_tool(
        "prepare_transfer",
        ctx,
        {
            "beneficiaryId": beneficiary_id,
            "amountPaise": int(amount),
            "currency": currency,
            "idempotencyKey": idem,
        },
    )


def _cancel_transfer(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    from app.services import transfer_service

    approval_id = (args.get("approvalId") or args.get("id") or "").strip()
    if not approval_id:
        raise AppError("An approval id is required.", code="VALIDATION_ERROR", status=422)
    return transfer_service.cancel(ctx.session, approval_id=approval_id, user_id=ctx.user_id, request_id=ctx.request_id)


def _pick(args: dict[str, Any], keys: set[str]) -> dict[str, Any]:
    return {k: args[k] for k in keys if k in args and args[k] not in (None, "")}


_HANDLERS = {
    "get_account_balance": _get_account_balance,
    "get_account_summary": _get_account_summary,
    "list_transactions": _list_transactions,
    "get_transaction_details": _get_transaction_details,
    "get_transfer_status": _get_transfer_status,
    "get_monthly_spending": _get_monthly_spending,
    "get_category_spending": _get_category_spending,
    "list_beneficiaries": _list_beneficiaries,
    "prepare_transfer": _prepare_transfer,
    "cancel_transfer": _cancel_transfer,
}
