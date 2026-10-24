"""Aggregated API router."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import account, agent, beneficiaries, dashboard, health, spending, transactions, transfers

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(dashboard.router)
api_router.include_router(account.router)
api_router.include_router(transactions.router)
api_router.include_router(spending.router)
api_router.include_router(beneficiaries.router)
api_router.include_router(agent.router)
api_router.include_router(transfers.router)
