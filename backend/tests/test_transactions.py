"""Transaction pagination and filter tests."""
from __future__ import annotations


def test_transaction_pagination(client):
    r = client.get("/api/v1/transactions?page=1&pageSize=2")
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) <= 2
    assert body["meta"]["pageSize"] == 2
    assert body["meta"]["total"] >= 4


def test_transaction_category_filter(client):
    # Current-month dining transactions only.
    r = client.get("/api/v1/transactions?category=Dining&pageSize=100")
    assert r.status_code == 200
    body = r.json()
    assert all(item["category"] == "Dining" for item in body["items"])
    # Exactly 2 current-month dining txns (Trattoria + Brew Room).
    current = [i for i in body["items"] if i["reference"].startswith("HMS-DEMO") and not "PREV" in i["reference"]]
    assert len(current) == 2


def test_transaction_merchant_search(client):
    r = client.get("/api/v1/transactions?merchant=Shopping Store")
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["merchant"] == "Shopping Store"


def test_transaction_detail(client):
    listing = client.get("/api/v1/transactions?pageSize=10").json()
    tid = listing["items"][0]["id"]
    r = client.get(f"/api/v1/transactions/{tid}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == tid
    assert "reference" in body


def test_transaction_not_found(client):
    r = client.get("/api/v1/transactions/does_not_exist")
    assert r.status_code == 404
