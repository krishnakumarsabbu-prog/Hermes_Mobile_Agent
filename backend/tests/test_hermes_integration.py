"""Hermes Agent Gateway integration tests.

These tests exercise the assistant service with the Gateway enabled but the
network layer mocked, so we verify the integration wiring (Hermes first,
orchestrator fallback, tool-call approval extraction, conversation
isolation) without needing a live Hermes process. Tool execution uses the
real backend tool bridge so approvals and balances are grounded.
"""
from __future__ import annotations

import pytest

from app.services import hermes_client


@pytest.fixture()
def gateway_enabled(monkeypatch):
    monkeypatch.setenv("HERMES_GATEWAY_ENABLED", "true")
    monkeypatch.setenv("HERMES_GATEWAY_BASE_URL", "http://127.0.0.1:8642")
    monkeypatch.setenv("HERMES_GATEWAY_MODEL", "hermes-3")
    from app.core import config as config_module

    config_module.get_settings.cache_clear()
    yield
    config_module.get_settings.cache_clear()


def test_hermes_response_is_returned(client, gateway_enabled, monkeypatch):
    async def fake_chat(*, messages, conversation_id, request_id, user_id, tool_executor=None):
        return hermes_client.HermesResult(
            content="Your current balance is ₹1,00,000.00.",
            tool_calls_made=[{"tool": "get_account_balance", "status": "ok", "callId": "c1"}],
            raw={},
        )

    monkeypatch.setattr(hermes_client, "chat", fake_chat)

    r = client.post("/api/v1/agent/chat", json={"message": "What is my account balance?"})
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "normal"
    assert "₹1,00,000.00" in body["text"]
    assert body["conversationId"]


def test_hermes_unavailable_falls_back_to_orchestrator(client, gateway_enabled, monkeypatch):
    async def fake_chat(*, messages, conversation_id, request_id, user_id, tool_executor=None):
        raise hermes_client.HermesError(
            "The assistant is unavailable right now.", code="HERMES_UNREACHABLE"
        )

    monkeypatch.setattr(hermes_client, "chat", fake_chat)

    r = client.post("/api/v1/agent/chat", json={"message": "Show me my spending this month"})
    assert r.status_code == 200
    body = r.json()
    assert "offline assistant" in body["text"]
    assert body["conversationId"]


def test_hermes_prepare_transfer_surfaces_approval(client, gateway_enabled, monkeypatch):
    ravi_id = client.get("/api/v1/beneficiaries?search=ravi").json()["items"][0]["id"]

    async def fake_chat(*, messages, conversation_id, request_id, user_id, tool_executor=None):
        assert tool_executor is not None
        approval = await tool_executor(
            {"name": "prepare_transfer",
             "args": {"beneficiaryId": ravi_id, "amountPaise": 100000, "currency": "INR",
                        "idempotencyKey": "hermes-test-1"}},
            "c1",
        )
        return hermes_client.HermesResult(
            content=f"I have prepared a simulated transfer of ₹1,000.00 to {approval['beneficiary']['fullName']}. Please review and authorize it.",
            tool_calls_made=[{"tool": "prepare_transfer", "status": "ok", "callId": "c1"}],
            raw={},
        )

    monkeypatch.setattr(hermes_client, "chat", fake_chat)

    r = client.post(
        "/api/v1/agent/chat",
        json={"message": "Transfer ₹1,000 to Ravi", "intentId": "hermes-test-1"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "transfer_approval"
    assert body["approval"]["status"] == "WAITING_FOR_APPROVAL"
    assert body["approval"]["beneficiary"]["fullName"] == "Ravi Sharma"
    balance = client.get("/api/v1/account/balance").json()["balancePaise"]
    assert balance == 10000000


def test_conversation_isolation_across_users(client, gateway_enabled, monkeypatch):
    async def fake_chat(*, messages, conversation_id, request_id, user_id, tool_executor=None):
        return hermes_client.HermesResult(content="ok", tool_calls_made=[], raw={})

    monkeypatch.setattr(hermes_client, "chat", fake_chat)

    r1 = client.post("/api/v1/agent/chat", json={"message": "hi"}, headers={"X-Hermes-Dev-User": "usr_01"})
    conv1 = r1.json()["conversationId"]
    r2 = client.post(
        "/api/v1/agent/chat",
        json={"message": "hi", "conversationId": conv1},
        headers={"X-Hermes-Dev-User": "usr_02"},
    )
    assert r2.status_code == 404


def test_hermes_empty_content_falls_back(client, gateway_enabled, monkeypatch):
    async def fake_chat(*, messages, conversation_id, request_id, user_id, tool_executor=None):
        return hermes_client.HermesResult(content="", tool_calls_made=[], raw={})

    monkeypatch.setattr(hermes_client, "chat", fake_chat)

    r = client.post("/api/v1/agent/chat", json={"message": "Show my spending this month"})
    assert r.status_code == 200
    body = r.json()
    assert "grounded offline view" in body["text"]


def test_gateway_disabled_uses_orchestrator(client, monkeypatch):
    called = {"value": False}

    async def fake_chat(**kwargs):
        called["value"] = True
        return hermes_client.HermesResult(content="should not happen", tool_calls_made=[], raw={})

    monkeypatch.setattr(hermes_client, "chat", fake_chat)

    r = client.post("/api/v1/agent/chat", json={"message": "Show my spending this month"})
    assert r.status_code == 200
    assert called["value"] is False
    assert r.json()["kind"] == "analysis"
