"""Transaction tools: recent and filtered history."""
from __future__ import annotations

from app.services import transaction_service
from app.tools.registry import register


@register("list_transactions", "List recent transactions.")
def list_transactions(ctx, args) -> dict:
    params = {"page": args.get("page", 1), "pageSize": args.get("pageSize", 10)}
    if args.get("category"):
        params["category"] = args["category"]
    return transaction_service.list_transactions(ctx.session, ctx.user_id, params)
