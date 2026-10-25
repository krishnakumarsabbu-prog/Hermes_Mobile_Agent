"""Tests for the explicit approve_transfer / reject_transfer chat actions.

These mirror the existing confirm_transfer tests but exercise the new
approve/reject branches which route through _handle_approval_decision and
return kind=transfer_result with authoritative backend status.
"""
from __future__ import annotations

from app.services import hermes_client
from app.core.database import session_scope
from app.models.approval import TransferApproval


def _prepare_pending(client):
    prep = client.post("/api/v1/agent/chat", json={"message": "Transfer ₹500 to Ravi"}).json()
    assert prep["kind"] == "transfer_approval"
    return prep["approval"]["approvalId"], prep["conversationId"]


def test_approve_authorizes_pending_transfer(client):
    approval_id, conv_id = _prepare_pending(client)
    bal_before = client.get("/api/v1/account/balance").json()["balancePaise"]

    r = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Approve transfer of ₹500 to Ravi",
            "conversationId": conv_id,
            "action": {"type": "approve_transfer", "approvalId": approval_id},
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "transfer_result"
    assert body["conversationId"] == conv_id
    assert body["approval"]["approvalId"] == approval_id
    assert body["approval"]["status"] == "COMPLETED"
    assert body["approval"]["consumed"] is True

    bal_after = client.get("/api/v1/account/balance").json()["balancePaise"]
    assert bal_before - bal_after == 50000


def test_approve_preserves_conversation_history(client):
    approval_id, conv_id = _prepare_pending(client)

    r = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Approve transfer",
            "conversationId": conv_id,
            "action": {"type": "approve_transfer", "approvalId": approval_id},
        },
    ).json()
    assert r["conversationId"] == conv_id

    history = client.get(f"/api/v1/agent/conversations/{conv_id}").json()
    assert len(history["messages"]) == 4
    assert history["messages"][3]["response"]["kind"] == "transfer_result"


def test_reject_cancels_pending_transfer(client):
    approval_id, conv_id = _prepare_pending(client)
    bal_before = client.get("/api/v1/account/balance").json()["balancePaise"]

    r = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Reject transfer of ₹500 to Ravi",
            "conversationId": conv_id,
            "action": {"type": "reject_transfer", "approvalId": approval_id},
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "transfer_result"
    assert body["approval"]["approvalId"] == approval_id
    assert body["approval"]["status"] == "CANCELLED"
    assert body["approval"]["consumed"] is True

    # No debit on reject
    bal_after = client.get("/api/v1/account/balance").json()["balancePaise"]
    assert bal_after == bal_before


def test_reject_preserves_conversation_history(client):
    approval_id, conv_id = _prepare_pending(client)

    r = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Reject transfer",
            "conversationId": conv_id,
            "action": {"type": "reject_transfer", "approvalId": approval_id},
        },
    ).json()
    assert r["conversationId"] == conv_id
    history = client.get(f"/api/v1/agent/conversations/{conv_id}").json()
    assert history["messages"][3]["response"]["kind"] == "transfer_result"


def test_approve_cannot_operate_on_another_users_approval(client):
    approval_id, _ = _prepare_pending(client)
    r = client.post(
        "/api/v1/agent/chat",
        headers={"X-Hermes-Dev-User": "synu_00001"},
        json={
            "message": "Approve transfer",
            "action": {"type": "approve_transfer", "approvalId": approval_id},
        },
    )
    assert r.status_code == 404


def test_reject_cannot_operate_on_another_users_approval(client):
    approval_id, _ = _prepare_pending(client)
    r = client.post(
        "/api/v1/agent/chat",
        headers={"X-Hermes-Dev-User": "synu_00001"},
        json={
            "message": "Reject transfer",
            "action": {"type": "reject_transfer", "approvalId": approval_id},
        },
    )
    assert r.status_code == 404


def test_approve_unknown_approval_rejected(client):
    r = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Approve transfer",
            "action": {"type": "approve_transfer", "approvalId": "appr_does_not_exist"},
        },
    )
    assert r.status_code == 404


def test_reject_cancelled_approval_rejected(client):
    approval_id, _ = _prepare_pending(client)
    client.post(f"/api/v1/transfers/{approval_id}/cancel")

    r = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Reject transfer",
            "action": {"type": "reject_transfer", "approvalId": approval_id},
        },
    )
    assert r.status_code == 409


def test_approve_expired_approval_rejected(client):
    approval_id, _ = _prepare_pending(client)
    with session_scope() as session:
        appr = session.get(TransferApproval, approval_id)
        appr.expires_at = "2020-01-01T00:00:00+00:00"
        session.flush()

    r = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Approve transfer",
            "action": {"type": "approve_transfer", "approvalId": approval_id},
        },
    )
    assert r.status_code == 409
    assert "expired" in r.json()["error"]["message"].lower()


def test_approve_retry_is_idempotent_no_duplicate_debit(client):
    approval_id, _ = _prepare_pending(client)
    bal_before = client.get("/api/v1/account/balance").json()["balancePaise"]

    payload = {
        "message": "Approve transfer",
        "action": {"type": "approve_transfer", "approvalId": approval_id},
    }
    r1 = client.post("/api/v1/agent/chat", json=payload)
    assert r1.status_code == 200
    bal_after_1 = client.get("/api/v1/account/balance").json()["balancePaise"]
    assert bal_before - bal_after_1 == 50000

    r2 = client.post("/api/v1/agent/chat", json=payload)
    # Retry hits the already-completed guard
    assert r2.status_code == 409
    bal_after_2 = client.get("/api/v1/account/balance").json()["balancePaise"]
    assert bal_after_2 == bal_after_1


def test_reject_retry_is_idempotent(client):
    approval_id, _ = _prepare_pending(client)
    bal_before = client.get("/api/v1/account/balance").json()["balancePaise"]

    payload = {
        "message": "Reject transfer",
        "action": {"type": "reject_transfer", "approvalId": approval_id},
    }
    r1 = client.post("/api/v1/agent/chat", json=payload)
    assert r1.status_code == 200
    assert r1.json()["approval"]["status"] == "CANCELLED"

    # Retry should not error and not change state
    r2 = client.post("/api/v1/agent/chat", json=payload)
    assert r2.status_code == 409
    bal_after = client.get("/api/v1/account/balance").json()["balancePaise"]
    assert bal_after == bal_before


def test_approve_after_reject_blocked(client):
    approval_id, _ = _prepare_pending(client)

    rej = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Reject transfer",
            "action": {"type": "reject_transfer", "approvalId": approval_id},
        },
    )
    assert rej.status_code == 200
    assert rej.json()["approval"]["status"] == "CANCELLED"

    appr = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Approve transfer",
            "action": {"type": "approve_transfer", "approvalId": approval_id},
        },
    )
    assert appr.status_code == 409


def test_reject_after_approve_blocked(client):
    approval_id, _ = _prepare_pending(client)

    appr = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Approve transfer",
            "action": {"type": "approve_transfer", "approvalId": approval_id},
        },
    )
    assert appr.status_code == 200
    assert appr.json()["approval"]["status"] == "COMPLETED"

    rej = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Reject transfer",
            "action": {"type": "reject_transfer", "approvalId": approval_id},
        },
    )
    assert rej.status_code == 409


def test_normal_chat_still_works_alongside_actions(client):
    r = client.post("/api/v1/agent/chat", json={"message": "What is my balance?"})
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] in ("normal", "analysis", "history", "clarification", "transfer_approval")
