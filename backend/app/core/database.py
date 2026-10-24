"""Database engine and session lifecycle.

Synchronous SQLAlchemy sessions over a persistent SQLite file. The event loop
is never blocked because route handlers run blocking work in the threadpool
that FastAPI/Starlette provides for sync endpoints (``def`` handlers, not
``async def``).
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def _build_engine(db_url: str) -> Engine:
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False, "timeout": 30},
        future=True,
        pool_pre_ping=True,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn: sqlite3.Connection, _record) -> None:
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA foreign_keys=ON;")
        cur.execute("PRAGMA busy_timeout=30000;")
        cur.execute("PRAGMA synchronous=NORMAL;")
        cur.close()

    return engine


_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = _build_engine(get_settings().db_url)
    return _engine


def get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False, future=True)
    return _SessionLocal


@contextmanager
def session_scope() -> Iterator[Session]:
    """A scoped session that commits on success and rolls back on error."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_engine_for_tests(db_url: str) -> None:
    """Replace the cached engine/session factory for an isolated test database."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = _build_engine(db_url)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False, future=True)


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a session per request.

    Commits on success, rolls back on error. This keeps service functions
    simple — they don't need to call commit() — while still giving each
    request a clean transaction boundary.
    """
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
