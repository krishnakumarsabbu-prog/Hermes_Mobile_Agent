"""MCP server configuration loaded from environment variables.

All values have safe local-development defaults. No secrets are hardcoded.
The backend base URL is validated and restricted to http(s) to avoid sending
credentials to unexpected hosts.
"""
from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="HERMES_MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # FastAPI backend base URL. Must be http or https.
    backend_base_url: str = Field(default="http://127.0.0.1:8000")

    # Development auth: user id forwarded via the backend's dev header.
    # This reuses the backend's existing dev authentication adapter. It is NOT
    # production auth and must be replaced with a verified-token scheme before
    # any real use. The value is never accepted from an LLM tool argument.
    dev_user_id: str = Field(default="usr_01")

    # Whether to send the dev-user header at all. Set to "false" when the
    # backend's default demo user is acceptable.
    send_dev_user_header: bool = Field(default=True)

    # HTTP client tuning (seconds).
    connect_timeout: float = Field(default=5.0, gt=0)
    read_timeout: float = Field(default=15.0, gt=0)

    # Maximum pagination size enforced client-side (mirrors backend max).
    max_page_size: int = Field(default=100, gt=0, le=500)

    # Maximum idempotency key length (mirrors backend constraint).
    max_idempotency_key_length: int = Field(default=120, gt=0)

    # Authorization tool is disabled by default. Even when enabled, the backend
    # enforces simulation-only safety; this flag only controls MCP exposure.
    enable_authorize_tool: bool = Field(default=False)

    # Request timeout for the whole MCP tool call (seconds).
    request_timeout: float = Field(default=20.0, gt=0)

    @field_validator("backend_base_url")
    @classmethod
    def _validate_url(cls, v: str) -> str:
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("backend_base_url must use http or https scheme")
        if not parsed.netloc:
            raise ValueError("backend_base_url must include a host")
        # No credentials embedded in the URL.
        if parsed.username or parsed.password:
            raise ValueError("backend_base_url must not contain credentials")
        return v.rstrip("/")


@lru_cache
def get_settings() -> ServerSettings:
    return ServerSettings()
