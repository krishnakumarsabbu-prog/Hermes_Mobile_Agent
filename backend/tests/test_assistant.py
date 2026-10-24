"""Assistant service tests for the canonical prompt."""
from __future__ import annotations


def test_assistant_spending_request(client):
    r = client.post("/api/v1/agent/chat", json={"message": "Show me my spending this month"})
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "analysis"
    assert "32,500" in body["text"]
    assert body["conversationId"]


def test_assistant_dining_request(client):
    r = client.post("/api/v1/agent/chat", json={"message": "How much on dining?"})
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "analysis"
    assert "6,200" in body["text"]


def test_assistant_canonical_transfer_prompt(client):
    r = client.post(
        "/api/v1/agent/chat",
        json={"message": "Show me my spending for this month, tell me how much I spent on dining, and transfer ₹75,000 to Ravi if I can afford it."},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "transfer_approval"
    assert body["approval"]["status"] == "WAITING_FOR_APPROVAL"
    assert body["approval"]["amountPaise"] == 7500000
    assert body["approval"]["beneficiary"]["fullName"] == "Ravi Sharma"
    assert body["summary"]["spendingPaise"] == 3250000
    assert body["summary"]["diningPaise"] == 620000
    assert body["summary"]["balancePaise"] == 10000000
    assert body["summary"]["proposedTransferPaise"] == 7500000
    assert body["summary"]["projectedBalancePaise"] == 2500000
    assert "32,500" in body["text"]
    assert "6,200" in body["text"]


def test_assistant_transfer_does_not_debit(client):
    before = client.get("/api/v1/account/balance").json()["balancePaise"]
    client.post(
        "/api/v1/agent/chat",
        json={"message": "Transfer ₹75,000 to Ravi"},
    )
    after = client.get("/api/v1/account/balance").json()["balancePaise"]
    assert before == after == 10000000


def test_assistant_conversation_persistence(client):
    r = client.post("/api/v1/agent/chat", json={"message": "Show my spending this month"})
    conv_id = r.json()["conversationId"]
    r2 = client.get(f"/api/v1/agent/conversations/{conv_id}")
    assert r2.status_code == 200
    body = r2.json()
    assert len(body["messages"]) == 2  # user + assistant
    assert body["messages"][0]["role"] == "user"
    assert body["messages"][1]["role"] == "assistant"
