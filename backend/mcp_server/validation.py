"""Input validation helpers shared by MCP tools.

Monetary values are kept as integer paise (no floating-point). Dates are
validated as YYYY-MM. Pagination is bounded. Idempotency keys are constrained.
"""
from __future__ import annotations

import re
from datetime import datetime

from mcp_server.errors import ToolValidationError

_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SORT_VALUES = {"asc", "desc"}
_VALID_CATEGORIES = {"Dining", "Shopping", "Utility", "Transfer"}
_VALID_STATUSES = {"successful", "pending", "failed"}


def validate_month(value: str | None, field: str = "month") -> str | None:
    if value is None or value == "":
        return None
    if not _MONTH_RE.match(value):
        raise ToolValidationError(f"{field} must be in YYYY-MM format.")
    try:
        datetime.strptime(value, "%Y-%m")
    except ValueError:
        raise ToolValidationError(f"{field} is not a valid month.")
    return value


def validate_date(value: str | None, field: str) -> str | None:
    if value is None or value == "":
        return None
    if not _DATE_RE.match(value):
        raise ToolValidationError(f"{field} must be in YYYY-MM-DD format.")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ToolValidationError(f"{field} is not a valid date.")
    return value


def validate_date_range(start: str | None, end: str | None) -> tuple[str | None, str | None]:
    s = validate_date(start, "startDate")
    e = validate_date(end, "endDate")
    if s and e and s > e:
        raise ToolValidationError("startDate must not be after endDate.")
    return s, e


def validate_pagination(page: int | None, page_size: int | None, max_page_size: int) -> tuple[int, int]:
    p = page if page is not None else 1
    ps = page_size if page_size is not None else 20
    if not isinstance(p, int) or p < 1:
        raise ToolValidationError("page must be a positive integer.")
    if not isinstance(ps, int) or ps < 1:
        raise ToolValidationError("pageSize must be a positive integer.")
    if ps > max_page_size:
        raise ToolValidationError(f"pageSize must not exceed {max_page_size}.")
    return p, ps


def validate_sort(value: str | None) -> str:
    v = (value or "desc").lower()
    if v not in _SORT_VALUES:
        raise ToolValidationError(f"sort must be one of: {', '.join(sorted(_SORT_VALUES))}.")
    return v


def validate_category(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    if value not in _VALID_CATEGORIES:
        raise ToolValidationError(f"category must be one of: {', '.join(sorted(_VALID_CATEGORIES))}.")
    return value


def validate_status(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    if value not in _VALID_STATUSES:
        raise ToolValidationError(f"status must be one of: {', '.join(sorted(_VALID_STATUSES))}.")
    return value


def validate_amount_paise(amount: int) -> int:
    if not isinstance(amount, int):
        raise ToolValidationError("amountPaise must be an integer (paise).")
    if amount <= 0:
        raise ToolValidationError("amountPaise must be a positive integer greater than zero.")
    return amount


def validate_idempotency_key(value: str, max_length: int) -> str:
    v = (value or "").strip()
    if not v:
        raise ToolValidationError("idempotencyKey is required.")
    if len(v) > max_length:
        raise ToolValidationError(f"idempotencyKey must not exceed {max_length} characters.")
    return v


def validate_beneficiary_id(value: str | None) -> str:
    v = (value or "").strip()
    if not v:
        raise ToolValidationError("beneficiaryId is required.")
    return v


def validate_approval_id(value: str | None) -> str:
    v = (value or "").strip()
    if not v:
        raise ToolValidationError("approvalId is required.")
    return v


def validate_search(value: str | None, max_length: int = 100) -> str | None:
    if value is None or value == "":
        return None
    v = value.strip()
    if len(v) > max_length:
        raise ToolValidationError(f"search must not exceed {max_length} characters.")
    return v
