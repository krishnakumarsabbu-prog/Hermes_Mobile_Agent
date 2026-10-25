"""FastAPI application entrypoint.

Run locally:
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

This is a local simulation backend. The dev auth adapter, SQLite database and
simulated transfers are NOT sufficient for real financial production use.
"""
from __future__ import annotations

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import install_exception_handlers
from app.core.logging import configure_logging
from app.core.database import get_engine
from app.middleware.request_id import RequestIdMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    # Ensure schema exists for first-run convenience. Migrations remain the
    # preferred path; this only creates tables if they don't already exist.
    from app.models.base import Base
    import app.models.account  # noqa: F401
    import app.models.beneficiary  # noqa: F401
    import app.models.transaction  # noqa: F401
    import app.models.approval  # noqa: F401
    import app.models.ledger  # noqa: F401
    import app.models.conversation  # noqa: F401
    import app.models.audit  # noqa: F401

    Base.metadata.create_all(get_engine())
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Hermes Personal Banking Simulation",
        description="Local FastAPI simulation backend. Not for real financial use.",
        version="2.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|10\.0\.2\.2)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Client-Info", "Apikey", "X-Hermes-Dev-User", "X-Request-Id"],
    )

    install_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
