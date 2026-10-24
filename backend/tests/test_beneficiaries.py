"""Beneficiary access boundary tests."""
from __future__ import annotations


def test_list_beneficiaries(client):
    r = client.get("/api/v1/beneficiaries")
    assert r.status_code == 200
    body = r.json()
    ids = [b["id"] for b in body["items"]]
    assert "ben_ravi" in ids
    assert "ben_priya" in ids


def test_get_beneficiary(client):
    r = client.get("/api/v1/beneficiaries/ben_ravi")
    assert r.status_code == 200
    body = r.json()
    assert body["fullName"] == "Ravi Sharma"
    assert body["alias"] == "Ravi"
    assert body["dailyLimitPaise"] == 10000000


def test_beneficiary_search(client):
    r = client.get("/api/v1/beneficiaries?search=Ravi")
    assert r.status_code == 200
    body = r.json()
    assert any(b["id"] == "ben_ravi" for b in body["items"])


def test_beneficiary_not_found(client):
    r = client.get("/api/v1/beneficiaries/ben_unknown")
    assert r.status_code == 404


def test_cross_user_beneficiary_rejected(client):
    # usr_02 does not own ben_ravi; the dev header selects a different user.
    r = client.get("/api/v1/beneficiaries/ben_ravi", headers={"X-Hermes-Dev-User": "synu_00001"})
    assert r.status_code == 404
