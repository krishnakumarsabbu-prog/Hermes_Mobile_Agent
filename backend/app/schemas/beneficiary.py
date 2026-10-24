"""Beneficiary schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class BeneficiaryOut(BaseModel):
    id: str
    fullName: str = Field(alias="fullName")
    alias: str
    dailyLimitPaise: int = Field(alias="dailyLimitPaise")
