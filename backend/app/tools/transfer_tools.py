"""Transfer tools: prepare a transfer approval (never debit)."""
from __future__ import annotations

from app.services import transfer_service
from app.tools.registry import register


@register("prepare_transfer", "Prepare a transfer approval without debiting.")
def prepare_transfer(ctx, args) -> dict:
    return transfer_service.prepare(
        ctx.session,
        user_id=ctx.user_id,
        beneficiary_id=args["beneficiaryId"],
        amount_paise=int(args["amountPaise"]),
        currency=args.get("currency", "INR"),
        idempotency_key=args["idempotencyKey"],
        request_id=ctx.request_id,
    )
