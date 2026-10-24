"""Account tools: balance and summary reads."""
from __future__ import annotations

from app.services import account_service
from app.tools.registry import register


@register("get_balance", "Read the current account balance.")
def get_balance(ctx, _args) -> dict:
    account = account_service.account_summary(ctx.session, ctx.user_id)
    return {"balancePaise": account.balance_paise, "accountId": account.id}


@register("get_account_summary", "Read the account summary.")
def get_account_summary(ctx, _args) -> dict:
    account = account_service.account_summary(ctx.session, ctx.user_id)
    return {
        "id": account.id,
        "name": account.name,
        "maskedNumber": account.masked_number,
        "balancePaise": account.balance_paise,
        "currency": account.currency,
    }
