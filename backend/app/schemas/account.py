"""Account and dashboard schemas."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class AccountSummary(BaseModel):
    id: str
    userId: str = Field(alias="userId")
    name: str
    maskedNumber: str = Field(alias="maskedNumber")
    balancePaise: int = Field(alias="balancePaise")
    currency: str = "INR"


class BalanceResponse(BaseModel):
    balancePaise: int = Field(alias="balancePaise")
    formattedINR: str = Field(alias="formattedINR")
    currency: str = "INR"


class DashboardSummary(BaseModel):
    userId: str = Field(alias="userId")
    accountId: str = Field(alias="accountId")
    balancePaise: int = Field(alias="balancePaise")
    formattedBalance: str = Field(alias="formattedBalance")
    currency: str = "INR"
    reportingMonth: str = Field(alias="reportingMonth")
    currentMonthExpenditurePaise: int = Field(alias="currentMonthExpenditurePaise")
    diningExpenditurePaise: int = Field(alias="diningExpenditurePaise")
    transactionCount: int = Field(alias="transactionCount")
    recentTransactions: List[dict] = Field(default_factory=list, alias="recentTransactions")
