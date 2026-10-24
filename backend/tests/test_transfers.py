"""Transfer lifecycle tests: prepare, authorize, cancel, status, errors."""
from __future__ import annotations

import time


def _prepare(client, amount_paise=7500000, beneficiary_id="ben_ravi", key="key-prepare-1"):
    return client.post(
        "/api/v1/transfers/prepare",
        json={
            "beneficiaryId": beneficiary_id,
            "amountPaise": amount_paise,
            "currency": "INR",
            "idempotencyKey": key,
        },
    )


def test_prepare_transfer(client):
    r = _prepare(client, key="key-prepare-basic")
    assert r.status_code == 200
    body = r.json()
    assert body["approvalId"].startswith("appr_")
    assert body["status"] == "WAITING_FOR_APPROVAL"
    assert body["amountPaise"] == 7500000
    assert body["currentBalancePaise"] == 10000000
    assert body["projectedBalancePaise"] == 2500000
    assert body["beneficiary"]["fullName"] == "Ravi Sharma"


def test_prepare_does_not_debit(client):
    before = client.get("/api/v1/account/balance").json()["balancePaise"]
    _prepare(client, key="key-no-debit")
    after = client.get("/api/v1/account/balance").json()["balancePaise"]
    assert before == after


def test_successful_transfer_after_approval(client):
    prep = _prepare(client, key="key-success").json()
    approval_id = prep["approvalId"]
    r = client.post(f"/api/v1/transfers/{approval_id}/authorize", json={"idempotencyKey": "key-auth-success"})
    assert r.status_code == 200
    body = r.json()
    assert body["approval"]["status"] == "COMPLETED"
    assert body["transaction"]["status"] == "successful"
    assert body["updatedBalancePaise"] == 2500000
    # Balance is actually debited.
    balance = client.get("/api/v1/account/balance").json()["balancePaise"]
    assert balance == 2500000
    # Exactly one current-month transfer transaction exists (prior-month seeded one excluded by date).
    from app.services.money import month_bounds
    start, end, _ = month_bounds()
    txns = client.get(f"/api/v1/transactions?category=Transfer&startDate={start}&endDate={end}").json()["items"]
    assert len(txns) == 1
    assert txns[0]["amountPaise"] == 7500000


def test_duplicate_authorization_cannot_debit_twice(client):
    prep = _prepare(client, key="key-dup").json()
    approval_id = prep["approvalId"]
    first = client.post(f"/api/v1/transfers/{approval_id}/authorize", json={"idempotencyKey": "key-auth-dup-1"})
    assert first.status_code == 200
    second = client.post(f"/api/v1/transfers/{approval_id}/authorize", json={"idempotencyKey": "key-auth-dup-2"})
    assert second.status_code == 409
    balance = client.get("/api/v1/account/balance").json()["balancePaise"]
    assert balance == 2500000  # debited only once


def test_idempotent_authorization_same_key(client):
    prep = _prepare(client, key="key-idem").json()
    approval_id = prep["approvalId"]
    first = client.post(f"/api/v1/transfers/{approval_id}/authorize", json={"idempotencyKey": "key-auth-idem"})
    assert first.status_code == 200
    second = client.post(f"/api/v1/transfers/{approval_id}/authorize", json={"idempotencyKey": "key-auth-idem"})
    assert second.status_code == 200
    # Same result, same balance.
    assert second.json()["updatedBalancePaise"] == 2500000
    balance = client.get("/api/v1/account/balance").json()["balancePaise"]
    assert balance == 2500000


def test_idempotency_conflict_different_payload(client):
    # Same idempotency key but different approval_id (different payload).
    prep1 = _prepare(client, amount_paise=3000000, key="key-conflict-src").json()
    prep2 = _prepare(client, amount_paise=2000000, key="key-conflict-src-2").json()
    r1 = client.post(f"/api/v1/transfers/{prep1['approvalId']}/authorize", json={"idempotencyKey": "key-conflict-shared"})
    assert r1.status_code == 200
    r2 = client.post(f"/api/v1/transfers/{prep2['approvalId']}/authorize", json={"idempotencyKey": "key-conflict-shared"})
    assert r2.status_code == 409
    assert r2.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_prepare_idempotency_same_key_returns_same_result(client):
    r1 = _prepare(client, key="key-prep-idem")
    assert r1.status_code == 200
    r2 = _prepare(client, key="key-prep-idem")
    assert r2.status_code == 200
    assert r1.json()["approvalId"] == r2.json()["approvalId"]


def test_cancellation_without_debit(client):
    prep = _prepare(client, key="key-cancel").json()
    approval_id = prep["approvalId"]
    before = client.get("/api/v1/account/balance").json()["balancePaise"]
    r = client.post(f"/api/v1/transfers/{approval_id}/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "CANCELLED"
    after = client.get("/api/v1/account/balance").json()["balancePaise"]
    assert before == after == 10000000


def test_insufficient_balance(client):
    # First lower the balance with a successful transfer, then attempt one
    # that exceeds the remaining balance but stays under the daily limit.
    prep = _prepare(client, amount_paise=9000000, key="key-lower-balance").json()
    client.post(f"/api/v1/transfers/{prep['approvalId']}/authorize", json={"idempotencyKey": "key-auth-lower"})
    # Balance is now 1,000,000 paise. Attempt 2,000,000 -> insufficient.
    r = _prepare(client, amount_paise=2000000, key="key-insufficient")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INSUFFICIENT_FUNDS"


def test_unknown_beneficiary(client):
    r = _prepare(client, beneficiary_id="ben_unknown", key="key-unknown-ben")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "BENEFICIARY_NOT_FOUND"


def test_amount_exceeding_daily_limit(client):
    # Set a beneficiary with a very low limit via a second user; instead test
    # the global daily limit by exceeding the configured 1,00,000 limit.
    r = _prepare(client, amount_paise=20000000, key="key-limit")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "TRANSFER_LIMIT_EXCEEDED"


def test_zero_or_negative_amount(client):
    r = _prepare(client, amount_paise=0, key="key-zero")
    assert r.status_code == 422
    r2 = _prepare(client, amount_paise=-100, key="key-negative")
    assert r2.status_code == 422


def test_cancel_completed_approval_rejected(client):
    prep = _prepare(client, key="key-cancel-completed").json()
    approval_id = prep["approvalId"]
    client.post(f"/api/v1/transfers/{approval_id}/authorize", json={"idempotencyKey": "key-auth-cc"})
    r = client.post(f"/api/v1/transfers/{approval_id}/cancel")
    assert r.status_code == 409


def test_transfer_status_completed(client):
    prep = _prepare(client, key="key-status").json()
    approval_id = prep["approvalId"]
    client.post(f"/api/v1/transfers/{approval_id}/authorize", json={"idempotencyKey": "key-auth-status"})
    r = client.get(f"/api/v1/transfers/{approval_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["approval"]["status"] == "COMPLETED"
    assert body["transaction"] is not None
    assert body["updatedBalancePaise"] == 2500000


def test_cross_user_approval_rejected(client):
    prep = _prepare(client, key="key-cross").json()
    approval_id = prep["approvalId"]
    r = client.get(f"/api/v1/transfers/{approval_id}", headers={"X-Hermes-Dev-User": "synu_00001"})
    assert r.status_code == 404


def test_expired_approval_rejected(client):
    # Prepare with a very short TTL by manipulating the DB directly.
    from app.core.database import session_scope
    from app.models.approval import TransferApproval
    from datetime import datetime, timedelta, timezone

    prep = _prepare(client, key="key-expired").json()
    approval_id = prep["approvalId"]
    with session_scope() as session:
        appr = session.get(TransferApproval, approval_id)
        appr.expires_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    r = client.post(f"/api/v1/transfers/{approval_id}/authorize", json={"idempotencyKey": "key-auth-expired"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "APPROVAL_EXPIRED"
    # Balance unchanged.
    balance = client.get("/api/v1/account/balance").json()["balancePaise"]
    assert balance == 10000000
