"""Tests for MCP tool discovery, schemas, and handler behavior with mocked HTTP."""
from __future__ import annotations

import httpx
import pytest

from mcp_server.errors import ToolValidationError
from mcp_server.tests.conftest import error_response, json_response
from mcp_server.tools import ALL_TOOLS, handler_for, tools_for_settings
from mcp_server.config import ServerSettings


def test_tool_discovery_returns_expected_names():
    settings = ServerSettings()
    tools = tools_for_settings(settings)
    names = [t.name for t, _ in tools]
    assert names == [
        "get_account_balance",
        "get_account_summary",
        "list_beneficiaries",
        "get_monthly_spending",
        "get_category_spending",
        "list_transactions",
        "get_transaction_details",
        "get_transfer_status",
        "prepare_transfer",
        "cancel_transfer",
    ]


def test_authorize_tool_not_registered():
    settings = ServerSettings()
    tools = tools_for_settings(settings)
    names = [t.name for t, _ in tools]
    assert "authorize_transfer" not in names
    assert "execute_payment" not in names


def test_every_tool_has_name_description_schema():
    for tool, _ in ALL_TOOLS:
        assert tool.name
        assert tool.description
        assert tool.inputSchema["type"] == "object"
        assert "properties" in tool.inputSchema


def test_prepare_transfer_requires_beneficiary_amount_key():
    tool = next(t for t, _ in ALL_TOOLS if t.name == "prepare_transfer")
    required = set(tool.inputSchema["required"])
    assert {"beneficiaryId", "amountPaise", "idempotencyKey"} <= required


def test_handler_for_unknown_returns_none():
    assert handler_for("nope", ServerSettings()) is None


@pytest.mark.asyncio
async def test_get_account_balance_handler(mock_client_factory, settings):
    def handler(req):
        return json_response({"balancePaise": 500, "formattedINR": "₹5.00", "currency": "INR"})

    client = mock_client_factory(handler)
    h = handler_for("get_account_balance", settings)
    result = await h(client, settings, {})
    assert result["balancePaise"] == 500
    await client.close()


@pytest.mark.asyncio
async def test_list_beneficiaries_handler_empty(mock_client_factory, settings):
    def handler(req):
        return json_response({"items": [], "meta": {"page": 1, "pageSize": 20, "total": 0, "totalPages": 0}})

    client = mock_client_factory(handler)
    h = handler_for("list_beneficiaries", settings)
    result = await h(client, settings, {})
    assert result["items"] == []
    assert result["meta"]["total"] == 0
    await client.close()


@pytest.mark.asyncio
async def test_list_beneficiaries_handler_search(mock_client_factory, settings):
    captured = {}

    def handler(req: httpx.Request):
        captured["params"] = dict(req.url.params)
        return json_response({"items": [{"id": "ben_1", "fullName": "Ravi"}], "meta": {"total": 1}})

    client = mock_client_factory(handler)
    h = handler_for("list_beneficiaries", settings)
    await h(client, settings, {"search": "ravi", "page": 1, "pageSize": 10})
    assert captured["params"]["search"] == "ravi"
    assert captured["params"]["pageSize"] == "10"
    await client.close()


@pytest.mark.asyncio
async def test_list_transactions_handler_filters(mock_client_factory, settings):
    captured = {}

    def handler(req: httpx.Request):
        captured["params"] = dict(req.url.params)
        return json_response({"items": [], "meta": {}})

    client = mock_client_factory(handler)
    h = handler_for("list_transactions", settings)
    await h(client, settings, {"category": "Dining", "status": "successful", "startDate": "2026-01-01", "endDate": "2026-01-31", "sort": "asc"})
    assert captured["params"]["category"] == "Dining"
    assert captured["params"]["status"] == "successful"
    assert captured["params"]["sort"] == "asc"
    await client.close()


@pytest.mark.asyncio
async def test_prepare_transfer_handler_forwards_body(mock_client_factory, settings):
    captured = {}

    def handler(req: httpx.Request):
        captured["body"] = __import__("json").loads(req.content)
        captured["path"] = req.url.path
        return json_response({"approvalId": "appr_1", "status": "WAITING_FOR_APPROVAL"})

    client = mock_client_factory(handler)
    h = handler_for("prepare_transfer", settings)
    result = await h(client, settings, {"beneficiaryId": "ben_ravi", "amountPaise": 7500000, "idempotencyKey": "key-1"})
    assert result["approvalId"] == "appr_1"
    assert captured["path"] == "/api/v1/transfers/prepare"
    assert captured["body"]["amountPaise"] == 7500000
    await client.close()


@pytest.mark.asyncio
async def test_prepare_transfer_never_calls_authorize(mock_client_factory, settings):
    paths = []

    def handler(req: httpx.Request):
        paths.append(req.url.path)
        if req.url.path == "/api/v1/transfers/prepare":
            return json_response({"approvalId": "appr_1", "status": "WAITING_FOR_APPROVAL"})
        return json_response({})

    client = mock_client_factory(handler)
    h = handler_for("prepare_transfer", settings)
    await h(client, settings, {"beneficiaryId": "ben_ravi", "amountPaise": 100, "idempotencyKey": "k"})
    assert not any("authorize" in p for p in paths)
    await client.close()


@pytest.mark.asyncio
async def test_prepare_transfer_rejects_zero_amount(mock_client_factory, settings):
    client = mock_client_factory(lambda req: json_response({}))
    h = handler_for("prepare_transfer", settings)
    with pytest.raises(ToolValidationError):
        await h(client, settings, {"beneficiaryId": "ben_1", "amountPaise": 0, "idempotencyKey": "k"})
    await client.close()


@pytest.mark.asyncio
async def test_prepare_transfer_rejects_missing_beneficiary(mock_client_factory, settings):
    client = mock_client_factory(lambda req: json_response({}))
    h = handler_for("prepare_transfer", settings)
    with pytest.raises(ToolValidationError):
        await h(client, settings, {"amountPaise": 100, "idempotencyKey": "k"})
    await client.close()


@pytest.mark.asyncio
async def test_prepare_transfer_rejects_missing_idempotency_key(mock_client_factory, settings):
    client = mock_client_factory(lambda req: json_response({}))
    h = handler_for("prepare_transfer", settings)
    with pytest.raises(ToolValidationError):
        await h(client, settings, {"beneficiaryId": "ben_1", "amountPaise": 100})
    await client.close()


@pytest.mark.asyncio
async def test_get_transfer_status_handler(mock_client_factory, settings):
    def handler(req):
        return json_response({"approval": {"approvalId": "appr_1", "status": "WAITING_FOR_APPROVAL"}})

    client = mock_client_factory(handler)
    h = handler_for("get_transfer_status", settings)
    result = await h(client, settings, {"approvalId": "appr_1"})
    assert result["approval"]["status"] == "WAITING_FOR_APPROVAL"
    await client.close()


@pytest.mark.asyncio
async def test_cancel_transfer_handler(mock_client_factory, settings):
    captured = {}

    def handler(req: httpx.Request):
        captured["method"] = req.method
        captured["path"] = req.url.path
        return json_response({"approvalId": "appr_1", "status": "CANCELLED"})

    client = mock_client_factory(handler)
    h = handler_for("cancel_transfer", settings)
    result = await h(client, settings, {"approvalId": "appr_1"})
    assert result["status"] == "CANCELLED"
    assert captured["method"] == "POST"
    assert captured["path"] == "/api/v1/transfers/appr_1/cancel"
    await client.close()


@pytest.mark.asyncio
async def test_invalid_category_rejected(mock_client_factory, settings):
    client = mock_client_factory(lambda req: json_response({}))
    h = handler_for("list_transactions", settings)
    with pytest.raises(ToolValidationError):
        await h(client, settings, {"category": "Gambling"})
    await client.close()


@pytest.mark.asyncio
async def test_backend_404_surfaces_as_backend_error(mock_client_factory, settings):
    def handler(req):
        return error_response("NOT_FOUND", "missing", 404)

    client = mock_client_factory(handler)
    h = handler_for("get_transaction_details", settings)
    from mcp_server.http_client import BackendError

    with pytest.raises(BackendError):
        await h(client, settings, {"transactionId": "txn_xxx"})
    await client.close()
