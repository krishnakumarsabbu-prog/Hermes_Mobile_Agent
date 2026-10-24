"""Beneficiary tools: resolution by name."""
from __future__ import annotations

from app.core.errors import AppError, BENEFICIARY_AMBIGUOUS, BENEFICIARY_NOT_FOUND
from app.repositories import beneficiary_repository
from app.tools.registry import register


@register("resolve_beneficiary", "Resolve a beneficiary by name.")
def resolve_beneficiary(ctx, args) -> dict:
    name = args.get("name", "").strip()
    if not name:
        raise AppError("A beneficiary name is required.", code=BENEFICIARY_NOT_FOUND, status=404)
    matches = beneficiary_repository.find_beneficiary_by_name(ctx.session, ctx.user_id, name)
    if not matches:
        raise AppError(f"I could not find a beneficiary matching '{name}'.", code=BENEFICIARY_NOT_FOUND, status=404)
    if len(matches) > 1:
        names = ", ".join(f"{b.full_name} ({b.alias})" for b in matches)
        raise AppError(f"Multiple beneficiaries match '{name}': {names}.", code=BENEFICIARY_AMBIGUOUS, status=409)
    b = matches[0]
    return {"id": b.id, "fullName": b.full_name, "alias": b.alias, "dailyLimitPaise": b.daily_limit_paise}
