"""Shared pytest fixtures: isolated temp SQLite DB per test run."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "test_hermes.db"
    monkeypatch.setenv("HERMES_DB_PATH", str(db_file))
    monkeypatch.setenv("HERMES_REPORTING_TIMEZONE", "Asia/Kolkata")
    monkeypatch.setenv("HERMES_DEV_USER_ID", "usr_01")
    # Small seed for fast test runs.
    monkeypatch.setenv("HERMES_SEED_USERS", "10")
    monkeypatch.setenv("HERMES_SEED_ACCOUNTS_MIN", "10")
    monkeypatch.setenv("HERMES_SEED_ACCOUNTS_MAX", "12")
    monkeypatch.setenv("HERMES_SEED_BENEFICIARIES", "20")
    monkeypatch.setenv("HERMES_SEED_TRANSACTIONS", "100")
    monkeypatch.setenv("HERMES_GATEWAY_ENABLED", "false")

    # Reset cached settings and engine so the new env takes effect.
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

    # Seed demo data only (small dataset for fast tests).
    from app.core.database import session_scope
    from app.seed.generator import generate
    with session_scope() as session:
        generate(session, reset=True)

    from app.main import create_app
    app = create_app()
    with TestClient(app) as c:
        yield c

    database_module.get_engine().dispose()
    config_module.get_settings.cache_clear()
