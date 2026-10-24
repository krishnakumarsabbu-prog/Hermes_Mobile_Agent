"""Tests for the MCP server: build, tool discovery, and call-tool dispatch."""
from __future__ import annotations

import json

import httpx
import pytest

from mcp_server.config import ServerSettings
from mcp_server.server import build_server
from mcp_server.tests.conftest import json_response


@pytest.mark.asyncio
async def test_server_builds_and_lists_tools(settings):
    """build_server registers tools and exposes a list_tools handler."""
    from mcp.types import ListToolsRequest

    server, client = build_server(settings)
    list_tools_fn = server.request_handlers.get(ListToolsRequest)
    assert list_tools_fn is not None
    result = await list_tools_fn(ListToolsRequest(method="tools/list"))
    names = [t.name for t in result.root.tools]
    assert "get_account_balance" in names
    assert len(names) == 10
    await client.close()


@pytest.mark.asyncio
async def test_call_tool_dispatches_to_handler(mock_client_factory, settings):
    """Verify the server's call_tool handler dispatches and wraps results."""
    def handler(req: httpx.Request) -> httpx.Response:
        return json_response({"balancePaise": 10000000, "formattedINR": "₹1,00,000.00", "currency": "INR"})

    mock = mock_client_factory(handler)
    server, client = build_server(settings)
    client._client = mock._client

    # The MCP Server stores request handlers internally. We invoke the call_tool
    # handler by reaching into the server's handler registry.
    from mcp.types import CallToolRequest, CallToolRequestParams

    # Find the call_tool handler the server registered.
    call_tool_fn = server.request_handlers.get(CallToolRequest)  # type: ignore[attr-defined]
    assert call_tool_fn is not None

    request = CallToolRequest(
        method="tools/call",
        params=CallToolRequestParams(name="get_account_balance", arguments={}),
    )
    result = await call_tool_fn(request)
    assert result.root.isError is False
    text = result.root.content[0].text
    payload = json.loads(text)
    assert payload["balancePaise"] == 10000000
    await mock.close()


@pytest.mark.asyncio
async def test_call_tool_unknown_tool_returns_error(mock_client_factory, settings):
    mock = mock_client_factory(lambda req: json_response({}))
    server, client = build_server(settings)
    client._client = mock._client

    from mcp.types import CallToolRequest, CallToolRequestParams

    call_tool_fn = server.request_handlers.get(CallToolRequest)  # type: ignore[attr-defined]
    request = CallToolRequest(
        method="tools/call",
        params=CallToolRequestParams(name="does_not_exist", arguments={}),
    )
    result = await call_tool_fn(request)
    assert result.root.isError is True
    await mock.close()


@pytest.mark.asyncio
async def test_call_tool_validation_error_returns_error(mock_client_factory, settings):
    mock = mock_client_factory(lambda req: json_response({}))
    server, client = build_server(settings)
    client._client = mock._client

    from mcp.types import CallToolRequest, CallToolRequestParams

    call_tool_fn = server.request_handlers.get(CallToolRequest)  # type: ignore[attr-defined]
    # Use a validation error our handler catches: an empty idempotencyKey passes
    # the SDK's required-property check but fails our validate_idempotency_key.
    request = CallToolRequest(
        method="tools/call",
        params=CallToolRequestParams(name="prepare_transfer", arguments={"beneficiaryId": "ben_1", "amountPaise": 100, "idempotencyKey": ""}),
    )
    result = await call_tool_fn(request)
    assert result.root.isError is True
    text = result.root.content[0].text
    payload = json.loads(text)
    assert "idempotencyKey" in payload["error"]
    await mock.close()


@pytest.mark.asyncio
async def test_call_tool_backend_error_returns_error(mock_client_factory, settings):
    from mcp_server.tests.conftest import error_response

    mock = mock_client_factory(lambda req: error_response("NOT_FOUND", "missing", 404))
    server, client = build_server(settings)
    client._client = mock._client

    from mcp.types import CallToolRequest, CallToolRequestParams

    call_tool_fn = server.request_handlers.get(CallToolRequest)  # type: ignore[attr-defined]
    request = CallToolRequest(
        method="tools/call",
        params=CallToolRequestParams(name="get_transaction_details", arguments={"transactionId": "txn_xxx"}),
    )
    result = await call_tool_fn(request)
    assert result.root.isError is True
    await mock.close()
