"""Application configuration loaded from environment variables.

All values have safe defaults so the backend runs out of the box for local
development. Nothing here is production-grade identity or transport security.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="HERMES_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db_path: str = "data/hermes.db"
    reporting_timezone: str = "Asia/Kolkata"
    cors_origins: str = "http://localhost:8081,http://localhost:19006,http://10.0.2.2:8081"
    dev_user_id: str = "usr_01"

    seed_users: int = 1000
    seed_accounts_min: int = 1000
    seed_accounts_max: int = 1500
    seed_beneficiaries: int = 5000
    seed_transactions: int = 100000

    approval_ttl_seconds: int = 300
    transfer_daily_limit_paise: int = 10000000  # ₹1,00,000

    max_page_size: int = 100
    default_page_size: int = 20

    @property
    def db_url(self) -> str:
        path = Path(self.db_path)
        if not path.is_absolute():
            path = BACKEND_DIR / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path.as_posix()}"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
