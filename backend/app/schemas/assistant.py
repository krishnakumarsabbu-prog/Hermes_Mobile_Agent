"""Assistant schemas — structured responses the frontend renders directly."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class TransferApprovalOut(BaseModel):
    approvalId: str = Field(alias="approvalId")
    beneficiary: dict
    amountPaise: int = Field(alias="amountPaise")
    sourceAccountId: str = Field(alias="sourceAccountId")
    currentBalancePaise: int = Field(alias="currentBalancePaise")
    projectedBalancePaise: int = Field(alias="projectedBalancePaise")
    expiresAt: str = Field(alias="expiresAt")
    status: str
    consumed: bool = False


class AssistantSummary(BaseModel):
    spendingPaise: int = Field(alias="spendingPaise")
    diningPaise: int = Field(alias="diningPaise")
    balancePaise: int = Field(alias="balancePaise")
    proposedTransferPaise: int = Field(alias="proposedTransferPaise")
    projectedBalancePaise: int = Field(alias="projectedBalancePaise")


class AssistantResponse(BaseModel):
    kind: Literal[
        "normal",
        "analysis",
        "history",
        "transfer_approval",
        "transfer_complete",
        "cancelled",
        "error",
    ]
    text: str
    approval: Optional[TransferApprovalOut] = None
    summary: Optional[AssistantSummary] = None
    conversationId: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    conversationId: Optional[str] = None
