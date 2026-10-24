"""Cross-user resource access rejection tests."""
from __future__ import annotations


def test_cross_user_account_rejected(client):
    r = client.get("/api/v1/account", headers={"X-Hermes-Dev-User": "synu_00001"})
    # Synthetic users have accounts, so this returns their account — verify it
    # is NOT the demo account.
    if r.status_code == 200:
        body = r.json()
        assert body["id"] != "acct_01"
    else:
        assert r.status_code == 404


def test_cross_user_transactions_rejected(client):
    # usr_01's transactions must not appear under a different user.
    r = client.get("/api/v1/transactions", headers={"X-Hermes-Dev-User": "synu_00001"})
    assert r.status_code == 200
    items = r.json()["items"]
    # None of the demo transaction references should appear.
    refs = {item["reference"] for item in items}
    assert "HMS-DEMO-TRAT" not in refs
    assert "HMS-DEMO-BREW" not in refs


def test_cross_user_spending_isolated(client):
    r = client.get("/api/v1/spending/monthly", headers={"X-Hermes-Dev-User": "synu_00001"})
    assert r.status_code == 200
    body = r.json()
    # The synthetic user has no current-month transactions (seeded outside the
    # current month), so totals must be zero and not the demo's 32,500.
    assert body["totalPaise"] == 0
