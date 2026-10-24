"""MCP tool definitions: schemas, handlers, and registration.

Each tool maps to a single existing FastAPI REST endpoint. Handlers validate
input client-side, call the backend through BackendClient, and return
structured JSON content. No tool exposes arbitrary URL access, shell execution,
or a user-identity argument.
"""
from __future__ import annotations

from typing import Any, Callable
from uuid import uuid4

from mcp.types import Tool

from mcp_server.config import ServerSettings
from mcp_server.errors import ToolError, ToolValidationError, text_result
from mcp_server.http_client import BackendClient, BackendError
from mcp_server.validation import (
    validate_amount_paise,
    validate_approval_id,
    validate_beneficiary_id,
    validate_category,
    validate_date_range,
    validate_idempotency_key,
    validate_month,
    validate_pagination,
    validate_search,
    validate_sort,
    validate_status,
)


ToolHandler = Callable[[BackendClient, ServerSettings, dict[str, Any]], Any]


def _tool(name: str, description: str, schema: dict[str, Any]) -> Tool:
    return Tool(name=name, description=description, inputSchema=schema)


# ---------------------------------------------------------------------------
# Read-only tools
# ---------------------------------------------------------------------------

GET_ACCOUNT_BALANCE = _tool(
    "get_account_balance",
    "Retrieve the authenticated user's current account balance in paise with "
    "the INR-formatted string. Use this when the user asks how much money they "
    "have or their current balance.",
    {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
)


async def handle_get_account_balance(client: BackendClient, settings: ServerSettings, args: dict[str, Any]) -> Any:
    return await client.get("/api/v1/account/balance")


GET_ACCOUNT_SUMMARY = _tool(
    "get_account_summary",
    "Return the authenticated user's account summary: account name, masked "
    "account number, currency, and balance in paise. Does not expose "
    "credentials or full account numbers.",
    {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
)


async def handle_get_account_summary(client: BackendClient, settings: ServerSettings, args: dict[str, Any]) -> Any:
    return await client.get("/api/v1/account")


LIST_BENEFICIARIES = _tool(
    "list_beneficiaries",
    "List beneficiaries authorized for the authenticated user, with optional "
    "name search and pagination. Returns items and pagination metadata. An "
    "empty list means no beneficiaries matched.",
    {
        "type": "object",
        "properties": {
            "search": {"type": "string", "description": "Optional substring to match against beneficiary name or alias."},
            "page": {"type": "integer", "minimum": 1, "description": "Page number, 1-indexed. Defaults to 1."},
            "pageSize": {"type": "integer", "minimum": 1, "maximum": 100, "description": "Items per page. Defaults to 20."},
        },
        "required": [],
        "additionalProperties": False,
    },
)


async def handle_list_beneficiaries(client: BackendClient, settings: ServerSettings, args: dict[str, Any]) -> Any:
    search = validate_search(args.get("search"))
    page, page_size = validate_pagination(args.get("page"), args.get("pageSize"), settings.max_page_size)
    params: dict[str, Any] = {"page": page, "pageSize": page_size}
    if search:
        params["search"] = search
    return await client.get("/api/v1/beneficiaries", params=params)


GET_MONTHLY_SPENDING = _tool(
    "get_monthly_spending",
    "Return the authenticated user's monthly expenditure total (paise), "
    "transaction count, and a per-category breakdown for the given month. "
    "If no month is supplied, the current reporting month is used.",
    {
        "type": "object",
        "properties": {
            "month": {"type": "string", "description": "Month in YYYY-MM format. Defaults to current month."},
        },
        "required": [],
        "additionalProperties": False,
    },
)


async def handle_get_monthly_spending(client: BackendClient, settings: ServerSettings, args: dict[str, Any]) -> Any:
    month = validate_month(args.get("month"))
    params: dict[str, Any] = {}
    if month:
        params["month"] = month
    return await client.get("/api/v1/spending/monthly", params=params)


GET_CATEGORY_SPENDING = _tool(
    "get_category_spending",
    "Return spending grouped by category with amounts in paise and percentage "
    "shares for the given month. If no month is supplied, the current reporting "
    "month is used.",
    {
        "type": "object",
        "properties": {
            "month": {"type": "string", "description": "Month in YYYY-MM format. Defaults to current month."},
        },
        "required": [],
        "additionalProperties": False,
    },
)


async def handle_get_category_spending(client: BackendClient, settings: ServerSettings, args: dict[str, Any]) -> Any:
    month = validate_month(args.get("month"))
    params: dict[str, Any] = {}
    if month:
        params["month"] = month
    return await client.get("/api/v1/spending/categories", params=params)


LIST_TRANSACTIONS = _tool(
    "list_transactions",
    "List the authenticated user's transaction history with pagination and "
    "optional filters: category, status, date range, merchant, reference, and "
    "sort order. Returns items and pagination metadata.",
    {
        "type": "object",
        "properties": {
            "page": {"type": "integer", "minimum": 1, "description": "Page number, 1-indexed. Defaults to 1."},
            "pageSize": {"type": "integer", "minimum": 1, "maximum": 100, "description": "Items per page. Defaults to 20."},
            "category": {"type": "string", "enum": ["Dining", "Shopping", "Utility", "Transfer"]},
            "status": {"type": "string", "enum": ["successful", "pending", "failed"]},
            "startDate": {"type": "string", "description": "Inclusive start date in YYYY-MM-DD format."},
            "endDate": {"type": "string", "description": "Inclusive end date in YYYY-MM-DD format."},
            "merchant": {"type": "string", "description": "Substring match on merchant name."},
            "reference": {"type": "string", "description": "Exact transaction reference."},
            "sort": {"type": "string", "enum": ["asc", "desc"], "description": "Sort by date. Defaults to desc."},
        },
        "required": [],
        "additionalProperties": False,
    },
)


async def handle_list_transactions(client: BackendClient, settings: ServerSettings, args: dict[str, Any]) -> Any:
    page, page_size = validate_pagination(args.get("page"), args.get("pageSize"), settings.max_page_size)
    category = validate_category(args.get("category"))
    status = validate_status(args.get("status"))
    start, end = validate_date_range(args.get("startDate"), args.get("endDate"))
    sort = validate_sort(args.get("sort"))
    merchant = args.get("merchant")
    reference = args.get("reference")
    params: dict[str, Any] = {"page": page, "pageSize": page_size, "sort": sort}
    if category:
        params["category"] = category
    if status:
        params["status"] = status
    if start:
        params["startDate"] = start
    if end:
        params["endDate"] = end
    if merchant:
        params["merchant"] = merchant
    if reference:
        params["reference"] = reference
    return await client.get("/api/v1/transactions", params=params)


GET_TRANSACTION_DETAILS = _tool(
    "get_transaction_details",
    "Retrieve a specific transaction by its id. Authorization and ownership are "
    "enforced by the backend; a transaction belonging to another user returns "
    "not found.",
    {
        "type": "object",
        "properties": {
            "transactionId": {"type": "string", "description": "The transaction identifier."},
        },
        "required": ["transactionId"],
        "additionalProperties": False,
    },
)


async def handle_get_transaction_details(client: BackendClient, settings: ServerSettings, args: dict[str, Any]) -> Any:
    tx_id = (args.get("transactionId") or "").strip()
    if not tx_id:
        raise ToolValidationError("transactionId is required.")
    return await client.get(f"/api/v1/transactions/{tx_id}")


GET_TRANSFER_STATUS = _tool(
    "get_transfer_status",
    "Retrieve the status, beneficiary, amount, projected balance, and expiration "
    "of a pending or completed transfer approval. Ownership is enforced by the "
    "backend; an approval belonging to another user returns not found.",
    {
        "type": "object",
        "properties": {
            "approvalId": {"type": "string", "description": "The transfer approval identifier."},
        },
        "required": ["approvalId"],
        "additionalProperties": False,
    },
)


async def handle_get_transfer_status(client: BackendClient, settings: ServerSettings, args: dict[str, Any]) -> Any:
    approval_id = validate_approval_id(args.get("approvalId"))
    return await client.get(f"/api/v1/transfers/{approval_id}")


# ---------------------------------------------------------------------------
# Transfer preparation (state-changing, does NOT execute/debit)
# ---------------------------------------------------------------------------

PREPARE_TRANSFER = _tool(
    "prepare_transfer",
    "Prepare a pending simulated transfer for a specific beneficiary and amount "
    "in paise. This creates an approval record but does NOT authorize or execute "
    "the transfer; no money is debited. Returns the approval id, beneficiary, "
    "amount, projected balance, and expiration. An idempotency key is required; "
    "reuse the same key to safely retry the identical request. The beneficiary "
    "must be specified by id, never inferred from an ambiguous name.",
    {
        "type": "object",
        "properties": {
            "beneficiaryId": {"type": "string", "description": "The exact beneficiary identifier."},
            "amountPaise": {"type": "integer", "minimum": 1, "description": "Transfer amount in integer paise (1 INR = 100 paise). Must be positive."},
            "currency": {"type": "string", "description": "ISO currency code. Defaults to INR.", "default": "INR"},
            "idempotencyKey": {"type": "string", "description": "Client-generated idempotency key. Reuse for safe retries of the same request."},
        },
        "required": ["beneficiaryId", "amountPaise", "idempotencyKey"],
        "additionalProperties": False,
    },
)


async def handle_prepare_transfer(client: BackendClient, settings: ServerSettings, args: dict[str, Any]) -> Any:
    beneficiary_id = validate_beneficiary_id(args.get("beneficiaryId"))
    amount = validate_amount_paise(args.get("amountPaise"))
    currency = (args.get("currency") or "INR").strip() or "INR"
    idem_key = validate_idempotency_key(args.get("idempotencyKey"), settings.max_idempotency_key_length)
    body = {
        "beneficiaryId": beneficiary_id,
        "amountPaise": amount,
        "currency": currency,
        "idempotencyKey": idem_key,
    }
    return await client.post("/api/v1/transfers/prepare", json=body)


# ---------------------------------------------------------------------------
# Optional cancellation tool
# ---------------------------------------------------------------------------

CANCEL_TRANSFER = _tool(
    "cancel_transfer",
    "Cancel an eligible pending transfer approval through the existing backend "
    "API. Only approvals still in a pending state may be cancelled. Does not "
    "claim success unless the backend confirms the cancellation.",
    {
        "type": "object",
        "properties": {
            "approvalId": {"type": "string", "description": "The transfer approval identifier to cancel."},
        },
        "required": ["approvalId"],
        "additionalProperties": False,
    },
)


async def handle_cancel_transfer(client: BackendClient, settings: ServerSettings, args: dict[str, Any]) -> Any:
    approval_id = validate_approval_id(args.get("approvalId"))
    return await client.post(f"/api/v1/transfers/{approval_id}/cancel", json={})


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

# Authorization is intentionally NOT registered here. It is disabled by default
# and must be added only behind a separately reviewed feature flag.

ALL_TOOLS: list[tuple[Tool, ToolHandler]] = [
    (GET_ACCOUNT_BALANCE, handle_get_account_balance),
    (GET_ACCOUNT_SUMMARY, handle_get_account_summary),
    (LIST_BENEFICIARIES, handle_list_beneficiaries),
    (GET_MONTHLY_SPENDING, handle_get_monthly_spending),
    (GET_CATEGORY_SPENDING, handle_get_category_spending),
    (LIST_TRANSACTIONS, handle_list_transactions),
    (GET_TRANSACTION_DETAILS, handle_get_transaction_details),
    (GET_TRANSFER_STATUS, handle_get_transfer_status),
    (PREPARE_TRANSFER, handle_prepare_transfer),
    (CANCEL_TRANSFER, handle_cancel_transfer),
]


def tools_for_settings(settings: ServerSettings) -> list[tuple[Tool, ToolHandler]]:
    return list(ALL_TOOLS)


def handler_for(name: str, settings: ServerSettings) -> ToolHandler | None:
    for tool, handler in ALL_TOOLS:
        if tool.name == name:
            return handler
    return None
