"""Transfer preparation and authorization schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, model_validator


class PrepareTransferRequest(BaseModel):
    beneficiaryId: str = Field(alias="beneficiaryId")
    amountPaise: int = Field(alias="amountPaise", gt=0)
    currency: str = Field(default="INR")
    idempotencyKey: str = Field(alias="idempotencyKey", min_length=1, max_length=120)


class AuthorizeTransferRequest(BaseModel):
    idempotencyKey: str = Field(alias="idempotencyKey", min_length=1, max_length=120)
    decision: str = Field(default="approve")


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


class TransferResultOut(BaseModel):
    approval: TransferApprovalOut
    transaction: Optional[dict] = None
    updatedBalancePaise: Optional[int] = Field(default=None, alias="updatedBalancePaise")


class TransferStatusOut(BaseModel):
    approval: TransferApprovalOut
    transaction: Optional[dict] = None
    updatedBalancePaise: Optional[int] = Field(default=None, alias="updatedBalancePaise")
