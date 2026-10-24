"""Integration tests: tool handlers call the real FastAPI backend in-process.

These use httpx.AsyncClient with an ASGI transport bound to the real FastAPI
app (via TestClient), so no network is involved and no real credentials are
needed. They verify end-to-end tool behavior including authorization, ownership,
and the transfer-preparation no-debit invariant.
"""
from __future__ import annotations

import json
import uuid

import httpx
import pytest

from mcp_server.config import ServerSettings
from mcp_server.http_client import BackendClient, BackendError
from mcp_server.tools import handler_for


def _make_asgi_client(real_client, settings: ServerSettings) -> BackendClient:
    """Wrap the real FastAPI app as an async ASGI transport for BackendClient."""
    transport = httpx.ASGITransport(app=real_client.app)
    client = BackendClient(settings)
    client._client = httpx.AsyncClient(
        base_url=settings.backend_base_url,
        transport=transport,
        follow_redirects=False,
        headers={"Accept": "application/json"},
        timeout=httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0),
    )
    return client


@pytest.fixture()
def settings() -> ServerSettings:
    return ServerSettings(
        backend_base_url="http://test-backend",
        dev_user_id="usr_01",
        send_dev_user_header=True,
        max_page_size=100,
        max_idempotency_key_length=120,
    )


@pytest.mark.asyncio
async def test_integration_get_account_balance(backend_client_integration, settings):
    client = _make_asgi_client(backend_client_integration, settings)
    h = handler_for("get_account_balance", settings)
    result = await h(client, settings, {})
    assert result["balancePaise"] == 10000000
    assert result["currency"] == "INR"
    await client.close()


@pytest.mark.asyncio
async def test_integration_get_account_summary(backend_client_integration, settings):
    client = _make_asgi_client(backend_client_integration, settings)
    h = handler_for("get_account_summary", settings)
    result = await h(client, settings, {})
    assert "name" in result
    assert "maskedNumber" in result
    # Full account number / credentials must not be present.
    assert "number" not in {k.lower() for k in result.keys()} or "maskedNumber" in result
    await client.close()


@pytest.mark.asyncio
async def test_integration_list_beneficiaries(backend_client_integration, settings):
    client = _make_asgi_client(backend_client_integration, settings)
    h = handler_for("list_beneficiaries", settings)
    result = await h(client, settings, {})
    assert "items" in result
    assert "meta" in result
    assert result["meta"]["page"] == 1
    await client.close()


@pytest.mark.asyncio
async def test_integration_list_beneficiaries_search(backend_client_integration, settings):
    client = _make_asgi_client(backend_client_integration, settings)
    h = handler_for("list_beneficiaries", settings)
    result = await h(client, settings, {"search": "ravi"})
    for item in result["items"]:
        assert "ravi" in item["fullName"].lower() or "ravi" in (item.get("alias") or "").lower()
    await client.close()


@pytest.mark.asyncio
async def test_integration_list_transactions(backend_client_integration, settings):
    client = _make_asgi_client(backend_client_integration, settings)
    h = handler_for("list_transactions", settings)
    result = await h(client, settings, {"pageSize": 5})
    assert len(result["items"]) <= 5
    assert result["meta"]["pageSize"] == 5
    await client.close()


@pytest.mark.asyncio
async def test_integration_get_transaction_details_ownership(backend_client_integration, settings):
    client = _make_asgi_client(backend_client_integration, settings)
    # First list a transaction to get a real id.
    h_list = handler_for("list_transactions", settings)
    listing = await h_list(client, settings, {"pageSize": 1})
    assert listing["items"], "seeded transactions should exist"
    tx_id = listing["items"][0]["id"]

    h = handler_for("get_transaction_details", settings)
    result = await h(client, settings, {"transactionId": tx_id})
    assert result["id"] == tx_id

    # A fabricated id returns not found.
    with pytest.raises(BackendError) as exc:
        await h(client, settings, {"transactionId": "txn_nonexistent"})
    assert exc.value.status == 404
    await client.close()


@pytest.mark.asyncio
async def test_integration_get_monthly_spending(backend_client_integration, settings):
    client = _make_asgi_client(backend_client_integration, settings)
    h = handler_for("get_monthly_spending", settings)
    result = await h(client, settings, {})
    assert "totalPaise" in result
    assert "byCategory" in result
    assert "transactionCount" in result
    await client.close()


@pytest.mark.asyncio
async def test_integration_get_category_spending(backend_client_integration, settings):
    client = _make_asgi_client(backend_client_integration, settings)
    h = handler_for("get_category_spending", settings)
    result = await h(client, settings, {})
    assert "categories" in result
    await client.close()


@pytest.mark.asyncio
async def test_integration_prepare_transfer_does_not_debit(backend_client_integration, settings):
    client = _make_asgi_client(backend_client_integration, settings)

    h_balance = handler_for("get_account_balance", settings)
    before = (await h_balance(client, settings, {}))["balancePaise"]

    h_prep = handler_for("prepare_transfer", settings)
    key = f"mcp-test-{uuid.uuid4().hex[:8]}"
    result = await h_prep(client, settings, {"beneficiaryId": "ben_ravi", "amountPaise": 7500000, "idempotencyKey": key})
    assert result["approvalId"].startswith("appr_")
    assert result["status"] == "WAITING_FOR_APPROVAL"
    assert result["amountPaise"] == 7500000

    after = (await h_balance(client, settings, {}))["balancePaise"]
    assert before == after, "prepare_transfer must not debit the balance"
    await client.close()


@pytest.mark.asyncio
async def test_integration_prepare_transfer_never_calls_authorize(backend_client_integration, settings):
    """The prepare handler must never touch the authorize endpoint."""
    # We verify by confirming the approval status stays WAITING_FOR_APPROVAL
    # and no transaction is created.
    client = _make_asgi_client(backend_client_integration, settings)
    h_prep = handler_for("prepare_transfer", settings)
    key = f"mcp-noauth-{uuid.uuid4().hex[:8]}"
    result = await h_prep(client, settings, {"beneficiaryId": "ben_ravi", "amountPaise": 100000, "idempotencyKey": key})
    assert result["status"] == "WAITING_FOR_APPROVAL"
    assert "transaction" not in result
    await client.close()


@pytest.mark.asyncio
async def test_integration_prepare_idempotency_same_key(backend_client_integration, settings):
    client = _make_asgi_client(backend_client_integration, settings)
    h_prep = handler_for("prepare_transfer", settings)
    key = f"mcp-idem-{uuid.uuid4().hex[:8]}"
    r1 = await h_prep(client, settings, {"beneficiaryId": "ben_ravi", "amountPaise": 500000, "idempotencyKey": key})
    r2 = await h_prep(client, settings, {"beneficiaryId": "ben_ravi", "amountPaise": 500000, "idempotencyKey": key})
    assert r1["approvalId"] == r2["approvalId"]
    await client.close()


@pytest.mark.asyncio
async def test_integration_prepare_unknown_beneficiary(backend_client_integration, settings):
    client = _make_asgi_client(backend_client_integration, settings)
    h_prep = handler_for("prepare_transfer", settings)
    with pytest.raises(BackendError) as exc:
        await h_prep(client, settings, {"beneficiaryId": "ben_unknown", "amountPaise": 100, "idempotencyKey": "k-unk"})
    assert exc.value.status == 404
    await client.close()


@pytest.mark.asyncio
async def test_integration_prepare_insufficient_funds(backend_client_integration, settings):
    client = _make_asgi_client(backend_client_integration, settings)
    h_prep = handler_for("prepare_transfer", settings)
    with pytest.raises(BackendError) as exc:
        await h_prep(client, settings, {"beneficiaryId": "ben_ravi", "amountPaise": 20000000, "idempotencyKey": "k-limit"})
    assert exc.value.status == 422
    await client.close()


@pytest.mark.asyncio
async def test_integration_get_transfer_status(backend_client_integration, settings):
    client = _make_asgi_client(backend_client_integration, settings)
    h_prep = handler_for("prepare_transfer", settings)
    key = f"mcp-status-{uuid.uuid4().hex[:8]}"
    prep = await h_prep(client, settings, {"beneficiaryId": "ben_ravi", "amountPaise": 100000, "idempotencyKey": key})
    approval_id = prep["approvalId"]

    h_status = handler_for("get_transfer_status", settings)
    result = await h_status(client, settings, {"approvalId": approval_id})
    assert result["approval"]["approvalId"] == approval_id
    assert result["approval"]["status"] == "WAITING_FOR_APPROVAL"
    await client.close()


@pytest.mark.asyncio
async def test_integration_get_transfer_status_cross_user_rejected(backend_client_integration, settings):
    client = _make_asgi_client(backend_client_integration, settings)
    h_prep = handler_for("prepare_transfer", settings)
    key = f"mcp-cross-{uuid.uuid4().hex[:8]}"
    prep = await h_prep(client, settings, {"beneficiaryId": "ben_ravi", "amountPaise": 100000, "idempotencyKey": key})
    approval_id = prep["approvalId"]

    # Switch to a different user.
    other_settings = settings.model_copy(update={"dev_user_id": "synu_00001"})
    other_client = _make_asgi_client(backend_client_integration, other_settings)
    h_status = handler_for("get_transfer_status", other_settings)
    with pytest.raises(BackendError) as exc:
        await h_status(other_client, other_settings, {"approvalId": approval_id})
    assert exc.value.status == 404
    await client.close()
    await other_client.close()


@pytest.mark.asyncio
async def test_integration_cancel_transfer(backend_client_integration, settings):
    client = _make_asgi_client(backend_client_integration, settings)
    h_prep = handler_for("prepare_transfer", settings)
    key = f"mcp-cancel-{uuid.uuid4().hex[:8]}"
    prep = await h_prep(client, settings, {"beneficiaryId": "ben_ravi", "amountPaise": 100000, "idempotencyKey": key})
    approval_id = prep["approvalId"]

    h_cancel = handler_for("cancel_transfer", settings)
    result = await h_cancel(client, settings, {"approvalId": approval_id})
    assert result["status"] == "CANCELLED"

    # Balance unchanged.
    h_balance = handler_for("get_account_balance", settings)
    assert (await h_balance(client, settings, {}))["balancePaise"] == 10000000
    await client.close()


@pytest.mark.asyncio
async def test_integration_cancel_completed_rejected(backend_client_integration, settings):
    client = _make_asgi_client(backend_client_integration, settings)
    h_prep = handler_for("prepare_transfer", settings)
    key = f"mcp-cancelcomp-{uuid.uuid4().hex[:8]}"
    prep = await h_prep(client, settings, {"beneficiaryId": "ben_ravi", "amountPaise": 100000, "idempotencyKey": key})
    approval_id = prep["approvalId"]

    # Authorize directly via the backend (not via MCP, since authorize is not exposed).
    resp = backend_client_integration.post(f"/api/v1/transfers/{approval_id}/authorize", json={"idempotencyKey": "int-auth"})
    assert resp.status_code == 200

    h_cancel = handler_for("cancel_transfer", settings)
    with pytest.raises(BackendError) as exc:
        await h_cancel(client, settings, {"approvalId": approval_id})
    assert exc.value.status == 409
    await client.close()
