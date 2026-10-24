"""Transaction schemas matching the frontend Transaction model."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

TransactionCategory = Literal["Dining", "Shopping", "Utility", "Transfer"]
TransactionStatus = Literal["successful", "pending", "cancelled", "failed"]


class TransactionOut(BaseModel):
    id: str
    merchant: str
    category: TransactionCategory
    amountPaise: int = Field(alias="amountPaise")
    date: str
    status: TransactionStatus
    reference: str
    note: Optional[str] = None


class TransactionDetail(TransactionOut):
    accountId: str = Field(alias="accountId")
    approvalId: Optional[str] = Field(default=None, alias="approvalId")
