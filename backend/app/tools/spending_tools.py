"""Spending tools: monthly and category totals."""
from __future__ import annotations

from app.services import spending_service
from app.tools.registry import register


@register("get_monthly_spending", "Monthly spending totals.")
def get_monthly_spending(ctx, args) -> dict:
    month = args.get("month")
    return spending_service.monthly_spending(ctx.session, ctx.user_id, month)


@register("get_category_spending", "Category spending breakdown.")
def get_category_spending(ctx, args) -> dict:
    month = args.get("month")
    return spending_service.category_summary(ctx.session, ctx.user_id, month)
