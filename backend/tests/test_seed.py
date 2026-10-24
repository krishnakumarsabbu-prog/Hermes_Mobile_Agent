"""Seed reproducibility, referential integrity, and persistence tests."""
from __future__ import annotations

from app.core.database import get_engine, session_scope
from app.models.base import Base
import app.models.account  # noqa: F401
import app.models.beneficiary  # noqa: F401
import app.models.transaction  # noqa: F401
import app.models.approval  # noqa: F401
import app.models.ledger  # noqa: F401
import app.models.conversation  # noqa: F401
import app.models.audit  # noqa: F401
from app.seed.generator import generate
from sqlalchemy import text


def test_seed_reproducibility_and_integrity(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DB_PATH", str(tmp_path / "seed.db"))
    monkeypatch.setenv("HERMES_REPORTING_TIMEZONE", "Asia/Kolkata")
    monkeypatch.setenv("HERMES_SEED_TRANSACTIONS", "500")
    monkeypatch.setenv("HERMES_SEED_USERS", "20")
    monkeypatch.setenv("HERMES_SEED_ACCOUNTS_MIN", "20")
    monkeypatch.setenv("HERMES_SEED_ACCOUNTS_MAX", "25")
    monkeypatch.setenv("HERMES_SEED_BENEFICIARIES", "60")

    from app.core import config as config_module
    config_module.get_settings.cache_clear()
    from app.core import database as database_module
    database_module.reset_engine_for_tests(f"sqlite:///{(tmp_path / 'seed.db').as_posix()}")
    Base.metadata.create_all(database_module.get_engine())

    with session_scope() as session:
        counts1 = generate(session, reset=True)
    with session_scope() as session:
        counts2 = generate(session, reset=True)
    # Deterministic seed => identical counts on reseed.
    assert counts1 == counts2

    with session_scope() as session:
        # Referential integrity: every transaction references a valid account.
        orphans = session.execute(text(
            "SELECT COUNT(*) FROM transactions t LEFT JOIN accounts a ON t.account_id = a.id WHERE a.id IS NULL"
        )).scalar()
        assert orphans == 0
        # Every beneficiary belongs to a valid user.
        ben_orphans = session.execute(text(
            "SELECT COUNT(*) FROM beneficiaries b LEFT JOIN users u ON b.user_id = u.id WHERE u.id IS NULL"
        )).scalar()
        assert ben_orphans == 0
        # Successful transfers have ledger entries.
        missing_ledger = session.execute(text(
            "SELECT COUNT(*) FROM transfer_approvals ap WHERE ap.status='COMPLETED' AND ap.transaction_id IS NOT NULL "
            "AND NOT EXISTS (SELECT 1 FROM ledger_entries le WHERE le.approval_id = ap.id)"
        )).scalar()
        assert missing_ledger == 0
        # Unique transaction references.
        dup_refs = session.execute(text(
            "SELECT COUNT(*) FROM (SELECT reference FROM transactions GROUP BY reference HAVING COUNT(*) > 1)"
        )).scalar()
        assert dup_refs == 0

    database_module.get_engine().dispose()
    config_module.get_settings.cache_clear()


def test_persistence_across_sessions(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DB_PATH", str(tmp_path / "persist.db"))
    monkeypatch.setenv("HERMES_REPORTING_TIMEZONE", "Asia/Kolkata")
    from app.core import config as config_module
    config_module.get_settings.cache_clear()
    from app.core import database as database_module
    database_module.reset_engine_for_tests(f"sqlite:///{(tmp_path / 'persist.db').as_posix()}")
    Base.metadata.create_all(database_module.get_engine())

    with session_scope() as session:
        generate(session, reset=True)
    # New session on same file should see the data.
    with session_scope() as session:
        from app.models.account import User
        assert session.query(User).filter(User.id == "usr_01").first() is not None

    database_module.get_engine().dispose()
    config_module.get_settings.cache_clear()
