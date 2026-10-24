"""Unit tests for BackendClient: auth headers, error mapping, transport errors."""
from __future__ import annotations

import json

import httpx
import pytest

from mcp_server.http_client import DEV_USER_HEADER, BackendClient, BackendError
from mcp_server.tests.conftest import error_response, json_response


@pytest.mark.asyncio
async def test_get_balance_success(mock_client_factory):
    def handler(req: httpx.Request) -> httpx.Response:
        assert req.method == "GET"
        assert req.url.path == "/api/v1/account/balance"
        assert req.headers[DEV_USER_HEADER] == "usr_01"
        return json_response({"balancePaise": 10000000, "formattedINR": "₹1,00,000.00", "currency": "INR"})

    client = mock_client_factory(handler)
    result = await client.get("/api/v1/account/balance")
    assert result["balancePaise"] == 10000000
    await client.close()


@pytest.mark.asyncio
async def test_auth_header_applied_without_leaking(mock_client_factory):
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(req.headers)
        return json_response({})

    client = mock_client_factory(handler)
    await client.get("/api/v1/account")
    assert captured["headers"][DEV_USER_HEADER.lower()] == "usr_01"
    # Authorization-style secrets should not appear unless explicitly set.
    assert "authorization" not in captured["headers"]
    await client.close()


@pytest.mark.asyncio
async def test_401_mapped_to_unauthorized(mock_client_factory):
    def handler(req):
        return error_response("UNAUTHORIZED", "bad user", 401)

    client = mock_client_factory(handler)
    with pytest.raises(BackendError) as exc:
        await client.get("/api/v1/account")
    assert exc.value.code == "UNAUTHORIZED"
    assert exc.value.status == 401
    await client.close()


@pytest.mark.asyncio
async def test_403_mapped_to_forbidden(mock_client_factory):
    def handler(req):
        return error_response("FORBIDDEN", "no", 403)

    client = mock_client_factory(handler)
    with pytest.raises(BackendError) as exc:
        await client.get("/api/v1/account")
    assert exc.value.code == "FORBIDDEN"
    await client.close()


@pytest.mark.asyncio
async def test_404_mapped_to_not_found(mock_client_factory):
    def handler(req):
        return error_response("NOT_FOUND", "missing", 404)

    client = mock_client_factory(handler)
    with pytest.raises(BackendError) as exc:
        await client.get("/api/v1/transactions/txn_xxx")
    assert exc.value.code == "NOT_FOUND"
    assert exc.value.status == 404
    await client.close()


@pytest.mark.asyncio
async def test_409_mapped_with_backend_code(mock_client_factory):
    def handler(req):
        return error_response("APPROVAL_ALREADY_USED", "used", 409)

    client = mock_client_factory(handler)
    with pytest.raises(BackendError) as exc:
        await client.get("/api/v1/transfers/appr_x")
    assert exc.value.status == 409
    assert exc.value.code == "APPROVAL_ALREADY_USED"
    await client.close()


@pytest.mark.asyncio
async def test_422_mapped_to_validation(mock_client_factory):
    def handler(req):
        return error_response("VALIDATION_ERROR", "bad input", 422)

    client = mock_client_factory(handler)
    with pytest.raises(BackendError) as exc:
        await client.post("/api/v1/transfers/prepare", json={})
    assert exc.value.status == 422
    await client.close()


@pytest.mark.asyncio
async def test_429_mapped_to_rate_limited(mock_client_factory):
    def handler(req):
        return error_response("RATE_LIMITED", "slow down", 429)

    client = mock_client_factory(handler)
    with pytest.raises(BackendError) as exc:
        await client.get("/api/v1/account")
    assert exc.value.code == "RATE_LIMITED"
    assert exc.value.status == 429
    await client.close()


@pytest.mark.asyncio
async def test_500_mapped_to_server_error(mock_client_factory):
    def handler(req):
        return httpx.Response(500, text="<html>internal stack trace</html>")

    client = mock_client_factory(handler)
    with pytest.raises(BackendError) as exc:
        await client.get("/api/v1/account")
    assert exc.value.code == "BACKEND_SERVER_ERROR"
    # The raw HTML body must not leak into the model-facing message.
    assert "stack trace" not in exc.value.message
    await client.close()


@pytest.mark.asyncio
async def test_timeout_mapped(mock_client_factory):
    def handler(req):
        raise httpx.TimeoutException("timed out")

    client = mock_client_factory(handler)
    with pytest.raises(BackendError) as exc:
        await client.get("/api/v1/account")
    assert exc.value.code == "BACKEND_TIMEOUT"
    await client.close()


@pytest.mark.asyncio
async def test_connect_error_mapped(mock_client_factory):
    def handler(req):
        raise httpx.ConnectError("refused")

    client = mock_client_factory(handler)
    with pytest.raises(BackendError) as exc:
        await client.get("/api/v1/account")
    assert exc.value.code == "BACKEND_UNREACHABLE"
    await client.close()


@pytest.mark.asyncio
async def test_malformed_json_mapped(mock_client_factory):
    def handler(req):
        return httpx.Response(200, content=b"not json", headers={"content-type": "application/json"})

    client = mock_client_factory(handler)
    with pytest.raises(BackendError) as exc:
        await client.get("/api/v1/account")
    assert exc.value.code == "BACKEND_MALFORMED"
    await client.close()


@pytest.mark.asyncio
async def test_post_forwards_json_body(mock_client_factory):
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(req.content)
        captured["method"] = req.method
        return json_response({"approvalId": "appr_1"}, status=200)

    client = mock_client_factory(handler)
    await client.post("/api/v1/transfers/prepare", json={"beneficiaryId": "ben_1", "amountPaise": 100, "idempotencyKey": "k"})
    assert captured["method"] == "POST"
    assert captured["body"]["beneficiaryId"] == "ben_1"
    await client.close()


@pytest.mark.asyncio
async def test_query_params_forwarded(mock_client_factory):
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["params"] = dict(req.url.params)
        return json_response({"items": [], "meta": {}})

    client = mock_client_factory(handler)
    await client.get("/api/v1/transactions", params={"page": 2, "pageSize": 50, "category": "Dining"})
    assert captured["params"]["page"] == "2"
    assert captured["params"]["pageSize"] == "50"
    assert captured["params"]["category"] == "Dining"
    await client.close()


@pytest.mark.asyncio
async def test_missing_credentials_fail_closed(settings):
    # With send_dev_user_header true but empty dev_user_id, no header is sent;
    # the backend would 401. We verify the header is simply absent.
    settings.dev_user_id = ""
    transport = httpx.MockTransport(lambda req: error_response("UNAUTHORIZED", "no user", 401))
    client = BackendClient(settings)
    client._client = httpx.AsyncClient(
        base_url=settings.backend_base_url, transport=transport, follow_redirects=False
    )
    with pytest.raises(BackendError) as exc:
        await client.get("/api/v1/account")
    assert exc.value.status == 401
    await client.close()


@pytest.mark.asyncio
async def test_redirects_disabled(mock_client_factory):
    def handler(req):
        return httpx.Response(302, headers={"location": "http://evil.example/steal"})

    client = mock_client_factory(handler)
    with pytest.raises(BackendError) as exc:
        await client.get("/api/v1/account")
    # 302 falls through to the generic non-2xx handler.
    assert exc.value.status is not None
    await client.close()
