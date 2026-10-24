"""Spending summary schemas."""
from __future__ import annotations

from typing import Dict

from pydantic import BaseModel, Field


class SpendingSummary(BaseModel):
    month: str
    totalPaise: int = Field(alias="totalPaise")
    byCategory: Dict[str, int] = Field(alias="byCategory")
    transactionCount: int = Field(alias="transactionCount")


class CategorySummary(BaseModel):
    month: str
    totalPaise: int = Field(alias="totalPaise")
    categories: list[dict] = Field(alias="categories")
    transactionCount: int = Field(alias="transactionCount")
