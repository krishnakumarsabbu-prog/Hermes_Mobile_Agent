"""Common schema helpers shared across response models."""
from __future__ import annotations

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageMeta(BaseModel):
    page: int = Field(ge=1)
    pageSize: int = Field(ge=1)
    total: int = Field(ge=0)
    totalPages: int = Field(ge=0)


class Page(BaseModel, Generic[T]):
    items: List[T]
    meta: PageMeta


class MoneyMixin(BaseModel):
    """Reminds readers that money fields are integer paise in all payloads."""

    model_config = {"populate_by_name": True}


def inr(paise: int) -> str:
    rupees = paise / 100
    return f"₹{rupees:,.2f}"
