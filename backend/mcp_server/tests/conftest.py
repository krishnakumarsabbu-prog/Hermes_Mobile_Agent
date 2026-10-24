"""Shared fixtures for MCP server tests.

Unit tests use a mocked transport via httpx.MockTransport. Integration tests
spin up the existing FastAPI backend with an isolated temp SQLite database,
mirroring the backend's own conftest.py conventions.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import httpx
import pytest

from mcp_server.config import ServerSettings
from mcp_server.http_client import BackendClient


@pytest.fixture()
def settings() -> ServerSettings:
    return ServerSettings(
        backend_base_url="http://test-backend",
        dev_user_id="usr_01",
        send_dev_user_header=True,
        max_page_size=100,
        max_idempotency_key_length=120,
    )


def _make_mock_client(
    settings: ServerSettings,
    handler: Callable[[httpx.Request], httpx.Response],
) -> BackendClient:
    """Build a BackendClient whose transport is fully mocked."""
    transport = httpx.MockTransport(handler)
    client = BackendClient(settings)
    # Inject the mock transport before any request is made.
    client._client = httpx.AsyncClient(
        base_url=settings.backend_base_url,
        transport=transport,
        follow_redirects=False,
        headers={"Accept": "application/json"},
        timeout=httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0),
    )
    return client


@pytest.fixture()
def mock_client_factory(settings: ServerSettings):
    """Return a factory that builds a BackendClient backed by a mock transport."""
    def _factory(handler: Callable[[httpx.Request], httpx.Response]) -> BackendClient:
        return _make_mock_client(settings, handler)
    return _factory


def json_response(payload: Any, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json=payload)


def error_response(code: str, message: str, status: int, request_id: str = "rid_test") -> httpx.Response:
    return httpx.Response(
        status,
        json={"error": {"code": code, "message": message, "requestId": request_id}},
    )


# ---------------------------------------------------------------------------
# Integration fixtures: real FastAPI backend in-process
# ---------------------------------------------------------------------------

@pytest.fixture()
def backend_client_integration(tmp_path: Path, monkeypatch):
    """Start the real FastAPI app with an isolated DB and yield (client, settings)."""
    db_file = tmp_path / "mcp_test_hermes.db"
    monkeypatch.setenv("HERMES_DB_PATH", str(db_file))
    monkeypatch.setenv("HERMES_REPORTING_TIMEZONE", "Asia/Kolkata")
    monkeypatch.setenv("HERMES_DEV_USER_ID", "usr_01")
    monkeypatch.setenv("HERMES_SEED_USERS", "10")
    monkeypatch.setenv("HERMES_SEED_ACCOUNTS_MIN", "10")
    monkeypatch.setenv("HERMES_SEED_ACCOUNTS_MAX", "12")
    monkeypatch.setenv("HERMES_SEED_BENEFICIARIES", "20")
    monkeypatch.setenv("HERMES_SEED_TRANSACTIONS", "100")

    from app.core import config as config_module
    config_module.get_settings.cache_clear()
    from app.core import database as database_module
    database_module.reset_engine_for_tests(f"sqlite:///{db_file.as_posix()}")

    from app.models.base import Base
    import app.models.account  # noqa: F401
    import app.models.beneficiary  # noqa: F401
    import app.models.transaction  # noqa: F401
    import app.models.approval  # noqa: F401
    import app.models.ledger  # noqa: F401
    import app.models.conversation  # noqa: F401
    import app.models.audit  # noqa: F401

    Base.metadata.create_all(database_module.get_engine())

    from app.core.database import session_scope
    from app.seed.generator import generate
    with session_scope() as session:
        generate(session, reset=True)

    from app.main import create_app
    from fastapi.testclient import TestClient
    app = create_app()
    with TestClient(app) as real_client:
        yield real_client

    database_module.get_engine().dispose()
    config_module.get_settings.cache_clear()
