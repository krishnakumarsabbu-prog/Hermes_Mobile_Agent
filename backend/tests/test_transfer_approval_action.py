"""Tests for transfer approval continuation and authoritative action handling in agent chat."""
from __future__ import annotations

from unittest.mock import AsyncMock
from app.services import hermes_client
from app.core.database import session_scope
from app.models.approval import TransferApproval


def test_valid_confirmation_authorizes_pending_transfer(client):
    # 1. Prepare transfer via chat
    prep = client.post("/api/v1/agent/chat", json={"message": "Transfer ₹500 to Ravi"}).json()
    assert prep["kind"] == "transfer_approval"
    approval_id = prep["approval"]["approvalId"]
    conv_id = prep["conversationId"]
    assert prep["approval"]["status"] == "WAITING_FOR_APPROVAL"

    bal_before = client.get("/api/v1/account/balance").json()["balancePaise"]

    # 2. Confirm transfer with explicit action
    conf = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Confirm transfer of ₹500 to Ravi",
            "conversationId": conv_id,
            "action": {
                "type": "confirm_transfer",
                "approvalId": approval_id,
            },
        },
    )
    assert conf.status_code == 200
    body = conf.json()
    assert body["kind"] == "transfer_complete"
    assert body["conversationId"] == conv_id
    assert body["approval"]["approvalId"] == approval_id
    assert body["approval"]["status"] == "COMPLETED"
    assert body["approval"]["consumed"] is True
    assert "transaction" in body
    assert body["transaction"]["amountPaise"] == 50000

    bal_after = client.get("/api/v1/account/balance").json()["balancePaise"]
    assert bal_before - bal_after == 50000


def test_confirmation_preserves_conversation_history(client):
    prep = client.post("/api/v1/agent/chat", json={"message": "Transfer ₹500 to Ravi"}).json()
    conv_id = prep["conversationId"]
    approval_id = prep["approval"]["approvalId"]

    conf = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Confirm transfer",
            "conversationId": conv_id,
            "action": {
                "type": "confirm_transfer",
                "approvalId": approval_id,
            },
        },
    ).json()
    assert conf["conversationId"] == conv_id

    # Verify conversation thread
    history = client.get(f"/api/v1/agent/conversations/{conv_id}").json()
    assert len(history["messages"]) == 4  # (user prep, asst prep, user conf, asst conf)
    assert history["messages"][0]["text"] == "Transfer ₹500 to Ravi"
    assert history["messages"][1]["response"]["kind"] == "transfer_approval"
    assert history["messages"][2]["text"] == "Confirm transfer"
    assert history["messages"][3]["response"]["kind"] == "transfer_complete"


def test_confirmation_cannot_operate_on_another_users_approval(client):
    # usr_01 creates approval
    prep = client.post("/api/v1/agent/chat", json={"message": "Transfer ₹500 to Ravi"}).json()
    approval_id = prep["approval"]["approvalId"]

    # synu_00001 attempts to confirm usr_01's approval
    r = client.post(
        "/api/v1/agent/chat",
        headers={"X-Hermes-Dev-User": "synu_00001"},
        json={
            "message": "Confirm transfer",
            "action": {
                "type": "confirm_transfer",
                "approvalId": approval_id,
            },
        },
    )
    assert r.status_code == 404
    assert "no longer available" in r.json()["error"]["message"]


def test_unknown_approval_rejected(client):
    r = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Confirm transfer",
            "action": {
                "type": "confirm_transfer",
                "approvalId": "appr_does_not_exist",
            },
        },
    )
    assert r.status_code == 404


def test_cancelled_or_consumed_approval_rejected(client):
    prep = client.post("/api/v1/agent/chat", json={"message": "Transfer ₹500 to Ravi"}).json()
    approval_id = prep["approval"]["approvalId"]

    # Cancel approval directly
    client.post(f"/api/v1/transfers/{approval_id}/cancel")

    # Attempt chat confirmation
    r = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Confirm transfer",
            "action": {
                "type": "confirm_transfer",
                "approvalId": approval_id,
            },
        },
    )
    assert r.status_code == 409
    assert "already been used" in r.json()["error"]["message"] or "cancelled" in r.json()["error"]["message"]


def test_expired_approval_rejected(client):
    prep = client.post("/api/v1/agent/chat", json={"message": "Transfer ₹500 to Ravi"}).json()
    approval_id = prep["approval"]["approvalId"]

    # Backdate expiration
    with session_scope() as session:
        appr = session.get(TransferApproval, approval_id)
        appr.expires_at = "2020-01-01T00:00:00+00:00"
        session.flush()

    r = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Confirm transfer",
            "action": {
                "type": "confirm_transfer",
                "approvalId": approval_id,
            },
        },
    )
    assert r.status_code == 409
    assert "expired" in r.json()["error"]["message"]


def test_retrying_confirmation_is_idempotent_no_duplicate_debit(client):
    prep = client.post("/api/v1/agent/chat", json={"message": "Transfer ₹500 to Ravi"}).json()
    approval_id = prep["approval"]["approvalId"]

    bal_before = client.get("/api/v1/account/balance").json()["balancePaise"]

    payload = {
        "message": "Confirm transfer",
        "action": {
            "type": "confirm_transfer",
            "approvalId": approval_id,
        },
    }

    # First confirmation
    r1 = client.post("/api/v1/agent/chat", json=payload)
    assert r1.status_code == 200
    bal_after_1 = client.get("/api/v1/account/balance").json()["balancePaise"]
    assert bal_before - bal_after_1 == 50000

    # Retry confirmation
    r2 = client.post("/api/v1/agent/chat", json=payload)
    assert r2.status_code == 200
    bal_after_2 = client.get("/api/v1/account/balance").json()["balancePaise"]
    # Balance must remain unchanged on retry
    assert bal_after_2 == bal_after_1


def test_hermes_cannot_fabricate_completed_status_when_approval_pending(client, monkeypatch):
    # Enable gateway for this test
    monkeypatch.setenv("HERMES_GATEWAY_ENABLED", "true")
    from app.core import config as config_module
    config_module.get_settings.cache_clear()

    # Model fabricates that it transferred the money without executing an authorization
    async def fake_lying_hermes(**kwargs):
        if "tool_executor" in kwargs and kwargs["tool_executor"]:
            await kwargs["tool_executor"](
                {
                    "name": "prepare_transfer",
                    "args": {
                        "beneficiaryId": "ben_ravi",
                        "amountPaise": 50000,
                        "currency": "INR",
                        "idempotencyKey": "k_lying_1",
                    },
                },
                "call_lying_1",
            )
        return hermes_client.HermesResult(
            content="I have transferred the ₹500.00 to Ravi Sharma and the transfer is completed.",
            tool_calls_made=[{"name": "prepare_transfer"}],
            raw={},
        )

    monkeypatch.setattr(hermes_client, "chat", fake_lying_hermes)

    r = client.post("/api/v1/agent/chat", json={"message": "Transfer ₹500 to Ravi"})
    assert r.status_code == 200
    body = r.json()

    # Authoritative backend status MUST remain transfer_approval (pending)
    assert body["kind"] == "transfer_approval"
    assert body["approval"]["status"] == "WAITING_FOR_APPROVAL"
    assert "pending" in body["text"].lower()

    # Balance must NOT be debited
    bal = client.get("/api/v1/account/balance").json()["balancePaise"]
    assert bal == 10000000
