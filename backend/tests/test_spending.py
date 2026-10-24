"""Spending summary tests for the canonical current-month scenario."""
from __future__ import annotations


def test_monthly_spending_canonical(client):
    r = client.get("/api/v1/spending/monthly")
    assert r.status_code == 200
    body = r.json()
    assert body["totalPaise"] == 3250000  # ₹32,500
    assert body["byCategory"]["Dining"] == 620000  # ₹6,200
    assert body["byCategory"]["Shopping"] == 1800000  # ₹18,000
    assert body["byCategory"]["Utility"] == 830000  # ₹8,300
    assert body["byCategory"]["Transfer"] == 0  # no current-month transfer
    assert body["transactionCount"] == 4


def test_category_summary(client):
    r = client.get("/api/v1/spending/categories")
    assert r.status_code == 200
    body = r.json()
    assert body["totalPaise"] == 3250000
    cats = {c["category"]: c for c in body["categories"]}
    assert cats["Dining"]["amountPaise"] == 620000
    assert cats["Dining"]["percentage"] == 19  # round(620000/3250000*100)
    assert cats["Shopping"]["percentage"] == 55
    assert cats["Utility"]["percentage"] == 26
