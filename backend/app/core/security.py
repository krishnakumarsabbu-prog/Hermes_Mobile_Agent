"""Development authentication adapter.

This is explicitly NOT production authentication. It resolves a seeded demo
user from a configurable development header / default, and can be replaced by a
real identity provider in a later phase. The effective user identity is always
derived from the request context, never from the request body.
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


@dataclass(frozen=True)
class AuthPrincipal:
    user_id: str


_DEV_HEADER = "x-hermes-dev-user"


def current_principal(
    dev_user: str | None = Header(default=None, alias=_DEV_HEADER),
) -> AuthPrincipal:
    """Resolve the authenticated principal from the dev adapter.

    For this POC the header is optional; when absent the configured demo user
    is used. A future phase must replace this with a verified token.
    """
    settings = get_settings()
    user_id = (dev_user or settings.dev_user_id).strip()
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return AuthPrincipal(user_id=user_id)
