"""Unit tests for input validation helpers."""
from __future__ import annotations

import pytest

from mcp_server.errors import ToolValidationError
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


def test_validate_month_valid():
    assert validate_month("2026-01") == "2026-01"


def test_validate_month_none():
    assert validate_month(None) is None


@pytest.mark.parametrize("bad", ["2026-13", "2026-1", "bad", "2026", "202601"])
def test_validate_month_invalid(bad):
    with pytest.raises(ToolValidationError):
        validate_month(bad)


def test_validate_date_range_valid():
    s, e = validate_date_range("2026-01-01", "2026-01-31")
    assert s == "2026-01-01"
    assert e == "2026-01-31"


def test_validate_date_range_reversed():
    with pytest.raises(ToolValidationError):
        validate_date_range("2026-02-01", "2026-01-01")


def test_validate_pagination_defaults():
    p, ps = validate_pagination(None, None, 100)
    assert (p, ps) == (1, 20)


def test_validate_pagination_over_max():
    with pytest.raises(ToolValidationError):
        validate_pagination(1, 200, 100)


def test_validate_pagination_zero_page():
    with pytest.raises(ToolValidationError):
        validate_pagination(0, 20, 100)


def test_validate_sort_default():
    assert validate_sort(None) == "desc"


def test_validate_sort_invalid():
    with pytest.raises(ToolValidationError):
        validate_sort("random")


def test_validate_category_valid():
    assert validate_category("Dining") == "Dining"


def test_validate_category_invalid():
    with pytest.raises(ToolValidationError):
        validate_category("Gambling")


def test_validate_status_valid():
    assert validate_status("successful") == "successful"


@pytest.mark.parametrize("bad", [0, -100])
def test_validate_amount_paise_nonpositive(bad):
    with pytest.raises(ToolValidationError):
        validate_amount_paise(bad)


def test_validate_amount_paise_non_integer():
    with pytest.raises(ToolValidationError):
        validate_amount_paise(1.5)  # type: ignore[arg-type]


def test_validate_idempotency_key_empty():
    with pytest.raises(ToolValidationError):
        validate_idempotency_key("", 120)


def test_validate_idempotency_key_too_long():
    with pytest.raises(ToolValidationError):
        validate_idempotency_key("x" * 200, 120)


def test_validate_beneficiary_id_empty():
    with pytest.raises(ToolValidationError):
        validate_beneficiary_id("")


def test_validate_approval_id_empty():
    with pytest.raises(ToolValidationError):
        validate_approval_id(None)


def test_validate_search_truncates_and_limits():
    assert validate_search("  ravi  ") == "ravi"
    with pytest.raises(ToolValidationError):
        validate_search("x" * 200)
