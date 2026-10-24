"""Dashboard and account summary tests."""
from __future__ import annotations


def test_account_summary(client):
    r = client.get("/api/v1/account")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "acct_01"
    assert body["userId"] == "usr_01"
    assert body["balancePaise"] == 10000000
    assert body["currency"] == "INR"


def test_account_balance(client):
    r = client.get("/api/v1/account/balance")
    assert r.status_code == 200
    body = r.json()
    assert body["balancePaise"] == 10000000
    assert "₹" in body["formattedINR"]


def test_dashboard_summary(client):
    r = client.get("/api/v1/dashboard/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["userId"] == "usr_01"
    assert body["balancePaise"] == 10000000
    assert body["currentMonthExpenditurePaise"] == 3250000
    assert body["diningExpenditurePaise"] == 620000
    assert body["transactionCount"] == 4
    assert len(body["recentTransactions"]) <= 5
