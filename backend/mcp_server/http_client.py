"""Asynchronous HTTP client wrapping the Hermes FastAPI backend.

Centralizes backend URL, authentication headers, timeouts, and error mapping.
Never logs authorization headers or secret values. Does not follow redirects
to unexpected hosts (redirects are disabled entirely for safety).
"""
from __future__ import annotations

import logging
from typing import Any, Mapping

import httpx

from mcp_server.config import ServerSettings

logger = logging.getLogger("hermes_mcp.http")

# Dev-auth header name consumed by app.core.security.current_principal.
DEV_USER_HEADER = "X-Hermes-Dev-User"


class BackendError(Exception):
    """Raised when the backend returns a non-2xx response or a transport error.

    Carries a safe, model-facing message plus an optional stable code. Never
    includes stack traces, tokens, or raw sensitive response bodies.
    """

    def __init__(self, message: str, *, code: str = "BACKEND_ERROR", status: int | None = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status


class BackendClient:
    """Thin async HTTP client for the Hermes backend REST API."""

    def __init__(self, settings: ServerSettings):
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._settings.backend_base_url,
                timeout=httpx.Timeout(
                    connect=self._settings.connect_timeout,
                    read=self._settings.read_timeout,
                    write=self._settings.connect_timeout,
                    pool=self._settings.connect_timeout,
                ),
                follow_redirects=False,
                headers={"Accept": "application/json"},
            )
        return self._client

    def _auth_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self._settings.send_dev_user_header:
            uid = (self._settings.dev_user_id or "").strip()
            if uid:
                headers[DEV_USER_HEADER] = uid
        return headers

    async def get(self, path: str, *, params: Mapping[str, Any] | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, *, json: Mapping[str, Any] | None = None) -> Any:
        return await self._request("POST", path, json=json)

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        client = await self._ensure_client()
        headers = self._auth_headers()
        try:
            response = await client.request(method, path, headers=headers, **kwargs)
        except httpx.TimeoutException:
            raise BackendError("The backend did not respond in time.", code="BACKEND_TIMEOUT")
        except httpx.ConnectError:
            raise BackendError("Could not connect to the backend.", code="BACKEND_UNREACHABLE")
        except httpx.HTTPError as exc:
            # Avoid leaking transport internals; log details at debug only.
            logger.debug("HTTP error for %s %s: %s", method, path, type(exc).__name__)
            raise BackendError("A network error occurred while contacting the backend.", code="BACKEND_NETWORK_ERROR")

        return self._handle_response(response, method, path)

    def _handle_response(self, response: httpx.Response, method: str, path: str) -> Any:
        status = response.status_code
        if 200 <= status < 300:
            if response.status_code == 204 or not response.content:
                return None
            try:
                return response.json()
            except Exception:
                logger.debug("Malformed JSON from %s %s", method, path)
                raise BackendError("The backend returned a malformed response.", code="BACKEND_MALFORMED")

        # Non-2xx: extract a safe message and code without leaking internals.
        code = "BACKEND_ERROR"
        message = "The backend request failed."
        try:
            body = response.json()
            err = body.get("error") if isinstance(body, dict) else None
            if isinstance(err, dict):
                code = str(err.get("code") or code)
                message = str(err.get("message") or message)
        except Exception:
            pass

        if status == 401:
            raise BackendError("Authentication failed. Check the configured user identity.", code="UNAUTHORIZED", status=401)
        if status == 403:
            raise BackendError("The authenticated user is not permitted to perform this action.", code="FORBIDDEN", status=403)
        if status == 404:
            raise BackendError("The requested resource was not found.", code="NOT_FOUND", status=404)
        if status == 409:
            raise BackendError(message or "A conflict occurred with the current state.", code=code, status=409)
        if status == 422:
            raise BackendError(message or "The request was invalid.", code=code or "VALIDATION_ERROR", status=422)
        if status == 429:
            raise BackendError("The backend rate limit was exceeded. Try again later.", code="RATE_LIMITED", status=429)
        if status >= 500:
            raise BackendError("The backend encountered an internal error.", code="BACKEND_SERVER_ERROR", status=status)
        raise BackendError(message, code=code, status=status)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def health(self) -> dict[str, Any]:
        return await self.get("/health/live")
