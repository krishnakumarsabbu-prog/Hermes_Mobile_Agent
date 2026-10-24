"""Shared API dependencies."""
from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import AuthPrincipal, current_principal
from app.middleware.request_id import get_request_id


def db_session():
    yield from get_db()


def principal(p: AuthPrincipal = Depends(current_principal)) -> AuthPrincipal:
    return p


def request_id_dep(request: Request) -> str:
    return get_request_id(request)
