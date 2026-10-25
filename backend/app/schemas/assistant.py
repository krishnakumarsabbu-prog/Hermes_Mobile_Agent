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
    idempotencyKey: Optional[str] = Field(default=None, alias="idempotencyKey")


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
        "transfer_result",
        "cancelled",
        "error",
        "clarification",
    ]
    text: str
    approval: Optional[TransferApprovalOut] = None
    summary: Optional[AssistantSummary] = None
    conversationId: Optional[str] = None


class ChatActionContext(BaseModel):
    """Client-supplied context for an approval action.

    These fields are informational only and let the frontend describe the
    approval it is acting on. The backend never trusts them as the source of
    truth for amount, beneficiary, ownership, or status; it always re-fetches
    the authoritative approval record by approvalId and validates it.
    """

    approvalId: Optional[str] = Field(default=None, alias="approvalId")
    beneficiaryId: Optional[str] = Field(default=None, alias="beneficiaryId")
    beneficiaryName: Optional[str] = Field(default=None, alias="beneficiaryName")
    amountPaise: Optional[int] = Field(default=None, alias="amountPaise")
    sourceAccountId: Optional[str] = Field(default=None, alias="sourceAccountId")
    status: Optional[str] = None


class ChatAction(BaseModel):
    type: Literal["confirm_transfer", "approve_transfer", "reject_transfer"] = "confirm_transfer"
    approvalId: str = Field(min_length=1, alias="approvalId")
    context: Optional[ChatActionContext] = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    conversationId: Optional[str] = None
    intentId: Optional[str] = None
    action: Optional[ChatAction] = None
