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


def test_assistant_missing_amount_requests_clarification(client):
    """Fix A: Never default to ₹75,000; ask for clarification when amount is missing."""
    # Direct transfer intent without amount
    r = client.post("/api/v1/agent/chat", json={"message": "Transfer to Ravi"})
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "clarification"
    assert "How much would you like to transfer" in body["text"]
    assert body.get("approval") is None

    # Composite intent without amount
    r2 = client.post(
        "/api/v1/agent/chat",
        json={"message": "Show me my spending for this month, tell me how much I spent on dining, and transfer to Ravi if I can afford it."},
    )
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["kind"] == "clarification"
    assert "32,500" in body2["text"]
    assert "6,200" in body2["text"]
    assert "How much would you like to transfer" in body2["text"]
    assert body2.get("approval") is None


def test_assistant_decimal_amount_parsing(client):
    """Fix A: Strict monetary parsing with decimal rupee support."""
    r = client.post("/api/v1/agent/chat", json={"message": "Transfer ₹500.50 to Ravi"})
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "transfer_approval"
    assert body["approval"]["amountPaise"] == 50050

    # More than 2 decimal digits is rejected as invalid fraction of paisa
    r_invalid = client.post("/api/v1/agent/chat", json={"message": "Transfer ₹50.125 to Ravi"})
    assert r_invalid.status_code == 200
    assert r_invalid.json()["kind"] == "clarification"


def test_assistant_intent_idempotency_distinct_and_retry(client):
    """Fix B: Each transfer intent gets a unique key; retries reuse the key."""
    # First genuine transfer proposal
    r1 = client.post(
        "/api/v1/agent/chat",
        json={"message": "Transfer ₹1,000 to Ravi", "intentId": "proposal-test-1"},
    )
    assert r1.status_code == 200
    body1 = r1.json()
    appr1_id = body1["approval"]["approvalId"]
    key1 = body1["approval"]["idempotencyKey"]
    assert "proposal-test-1" in key1

    # Retry of the same proposal with identical intentId reuses the key & approval
    r1_retry = client.post(
        "/api/v1/agent/chat",
        json={"message": "Transfer ₹1,000 to Ravi", "intentId": "proposal-test-1"},
    )
    assert r1_retry.status_code == 200
    assert r1_retry.json()["approval"]["approvalId"] == appr1_id
    assert r1_retry.json()["approval"]["idempotencyKey"] == key1

    # Genuinely new transfer intent gets a distinct key and new approval
    r2 = client.post(
        "/api/v1/agent/chat",
        json={"message": "Transfer ₹1,000 to Ravi", "intentId": "proposal-test-2"},
    )
    assert r2.status_code == 200
    body2 = r2.json()
    appr2_id = body2["approval"]["approvalId"]
    key2 = body2["approval"]["idempotencyKey"]
    assert appr2_id != appr1_id
    assert key2 != key1
