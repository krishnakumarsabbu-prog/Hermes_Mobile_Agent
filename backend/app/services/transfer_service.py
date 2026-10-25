"""Transfer service: prepare, authorize, cancel, status.

Authorization is atomic and uses conditional SQL to prevent double-debit under
concurrency. Preparation never debits. The approval binds the exact transfer
details and cannot be changed by the client.
"""
from __future__ import annotations

import uuid
from datetime import timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import (
    AppError,
    APPROVAL_ALREADY_USED,
    APPROVAL_EXPIRED,
    BENEFICIARY_NOT_FOUND,
    INSUFFICIENT_FUNDS,
    NotFoundError,
    TRANSFER_LIMIT_EXCEEDED,
    ValidationFailure,
)
from app.models.approval import (
    TransferApproval,
    APPROVAL_CANCELLED,
    APPROVAL_COMPLETED,
    APPROVAL_EXPIRED as MODEL_EXPIRED,
    APPROVAL_WAITING,
    PENDING_STATES,
)
from app.models.ledger import LedgerEntry, ENTRY_DEBIT
from app.models.transaction import Transaction, CATEGORY_TRANSFER, STATUS_SUCCESSFUL
from app.repositories import account_repository, approval_repository, beneficiary_repository
from app.services import audit_service, idempotency
from app.services.money import format_inr, now_utc_iso, utc_now


def prepare(session: Session, *, user_id: str, beneficiary_id: str, amount_paise: int, currency: str, idempotency_key: str, request_id: str = "") -> dict:
    if amount_paise <= 0:
        raise ValidationFailure("The transfer amount must be positive.")
    account = account_repository.get_account(session, user_id)
    if account is None:
        raise NotFoundError("No account found for this user.")
    beneficiary = beneficiary_repository.get_beneficiary(session, user_id, beneficiary_id)
    if beneficiary is None:
        raise AppError("Beneficiary not found.", code=BENEFICIARY_NOT_FOUND, status=404)

    settings = get_settings()
    if amount_paise > beneficiary.daily_limit_paise:
        raise AppError("This transfer exceeds the beneficiary daily limit.", code=TRANSFER_LIMIT_EXCEEDED, status=422)
    if amount_paise > settings.transfer_daily_limit_paise:
        raise AppError("This transfer exceeds the daily transfer limit.", code=TRANSFER_LIMIT_EXCEEDED, status=422)
    if amount_paise > account.balance_paise:
        raise AppError("This transfer exceeds your available balance.", code=INSUFFICIENT_FUNDS, status=422)

    # Idempotency: return prior result for same key+payload if not expired.
    existing = idempotency.lookup(session, idempotency_key, user_id)
    endpoint = "transfers/prepare"
    payload = {"beneficiaryId": beneficiary_id, "amountPaise": amount_paise, "currency": currency}
    if existing is not None and existing.endpoint == endpoint:
        idempotency.check_conflict(existing, payload)
        import json
        cached_resp = json.loads(existing.response_json)
        if not cached_resp.get("expiresAt") or utc_now() < _parse_iso(cached_resp["expiresAt"]):
            return cached_resp


    approval = TransferApproval(
        id=f"appr_{uuid.uuid4().hex[:20]}",
        user_id=user_id,
        source_account_id=account.id,
        beneficiary_id=beneficiary.id,
        amount_paise=amount_paise,
        currency=currency,
        status=APPROVAL_WAITING,
        created_at=now_utc_iso(),
        expires_at=(utc_now() + timedelta(seconds=settings.approval_ttl_seconds)).isoformat(),
        idempotency_key=idempotency_key,
        version=1,
    )
    session.add(approval)
    session.flush()

    audit_service.record(
        session, user_id=user_id, action="transfer.prepare", target=approval.id, detail=f"amount={amount_paise}", request_id=request_id
    )

    response = _approval_to_dict(approval, beneficiary, account.balance_paise)
    idempotency.save(
        session, key=idempotency_key, user_id=user_id, endpoint=endpoint, payload=payload, status_code=200, response=response
    )
    return response


def authorize(session: Session, *, approval_id: str, user_id: str, idempotency_key: str, request_id: str = "") -> dict:
    endpoint = "transfers/authorize"
    payload = {"approvalId": approval_id}
    existing = idempotency.lookup(session, idempotency_key, user_id)
    if existing is not None and existing.endpoint == endpoint:
        idempotency.check_conflict(existing, payload)
        import json
        return json.loads(existing.response_json)

    approval = approval_repository.get_approval_for_user(session, approval_id, user_id)
    if approval is None:
        raise NotFoundError("This approval is no longer available.")

    if approval.status == APPROVAL_COMPLETED:
        raise AppError("This approval has already been used.", code=APPROVAL_ALREADY_USED, status=409)
    if approval.status in (APPROVAL_CANCELLED, MODEL_EXPIRED):
        raise AppError(f"This approval is {approval.status.lower()} and cannot be authorized.", code=APPROVAL_ALREADY_USED, status=409)
    if approval.status not in PENDING_STATES:
        raise AppError(f"This approval is {approval.status.lower()} and cannot be authorized.", code=APPROVAL_ALREADY_USED, status=409)

    # Expiry check.
    if utc_now() > _parse_iso(approval.expires_at):
        approval.status = MODEL_EXPIRED
        approval.decision_at = now_utc_iso()
        audit_service.record(session, user_id=user_id, action="transfer.expired", target=approval.id, request_id=request_id)
        raise AppError("This approval has expired.", code=APPROVAL_EXPIRED, status=409)

    account = account_repository.get_account_by_id(session, approval.source_account_id)
    beneficiary = beneficiary_repository.get_beneficiary(session, user_id, approval.beneficiary_id)
    if beneficiary is None:
        raise AppError("Beneficiary not found.", code=BENEFICIARY_NOT_FOUND, status=404)

    # Revalidate funds and limits at authorization time.
    if approval.amount_paise > account.balance_paise:
        raise AppError("The available balance is no longer sufficient.", code=INSUFFICIENT_FUNDS, status=422)

    # --- Atomic claim via conditional UPDATE on the approval row. ---
    # Use the version field as a concurrency token: atomically flip a pending
    # approval to COMPLETED and bump the version in a single conditional UPDATE.
    # Only one caller can match the pending-status predicate; the rowcount tells
    # us whether we won the claim. This prevents double-debit under concurrency
    # without relying on a process-local lock.
    claimed = session.execute(
        text(
            "UPDATE transfer_approvals SET status = 'COMPLETED', decision_at = :now, version = version + 1 "
            "WHERE id = :aid AND status IN ('PREPARED','WAITING_FOR_APPROVAL')"
        ),
        {"aid": approval_id, "now": now_utc_iso()},
    ).rowcount
    if claimed == 0:
        # Another caller already claimed it or it's no longer pending.
        session.expire(approval)
        raise AppError("This approval is no longer pending.", code=APPROVAL_ALREADY_USED, status=409)

    # Conditional debit: only succeeds if the balance is still sufficient.
    # If this fails, the entire transaction (including the claim above) is
    # rolled back by session_scope, so the approval returns to pending.
    debited = session.execute(
        text(
            "UPDATE accounts SET balance_paise = balance_paise - :amt "
            "WHERE id = :aid AND balance_paise >= :amt"
        ),
        {"aid": account.id, "amt": approval.amount_paise},
    ).rowcount
    if debited == 0:
        raise AppError("The available balance is no longer sufficient.", code=INSUFFICIENT_FUNDS, status=422)

    txn_id = f"txn_transfer_{uuid.uuid4().hex[:16]}"
    reference = f"HMS-{utc_now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
    txn = Transaction(
        id=txn_id,
        account_id=account.id,
        merchant=beneficiary.full_name,
        category=CATEGORY_TRANSFER,
        amount_paise=approval.amount_paise,
        status=STATUS_SUCCESSFUL,
        reference=reference,
        note="Simulated transfer",
        occurred_at=now_utc_iso(),
        approval_id=approval.id,
    )
    session.add(txn)
    session.flush()

    ledger = LedgerEntry(
        id=f"led_{uuid.uuid4().hex[:20]}",
        account_id=account.id,
        approval_id=approval.id,
        transaction_id=txn.id,
        entry_type=ENTRY_DEBIT,
        amount_paise=approval.amount_paise,
        reference=reference,
        created_at=now_utc_iso(),
    )
    session.add(ledger)

    # Sync the ORM object with the conditional UPDATE already applied to the DB.
    session.expire(approval)
    approval = approval_repository.get_approval(session, approval_id)
    approval.transaction_id = txn_id
    session.flush()

    audit_service.record(
        session, user_id=user_id, action="transfer.authorize", target=approval.id, detail=f"txn={txn_id}", request_id=request_id
    )

    # Refresh balance from DB.
    session.flush()
    session.expire(account)
    new_balance = account_repository.get_account_by_id(session, account.id).balance_paise

    response = {
        "approval": _approval_to_dict(approval, beneficiary, new_balance, consumed=True),
        "transaction": {
            "id": txn.id,
            "merchant": txn.merchant,
            "category": txn.category,
            "amountPaise": txn.amount_paise,
            "date": txn.occurred_at,
            "status": txn.status,
            "reference": txn.reference,
            "note": txn.note,
        },
        "updatedBalancePaise": new_balance,
    }
    idempotency.save(
        session, key=idempotency_key, user_id=user_id, endpoint=endpoint, payload=payload, status_code=200, response=response
    )
    return response


def cancel(
    session: Session,
    *,
    approval_id: str,
    user_id: str,
    request_id: str = "",
    idempotency_key: str | None = None,
) -> dict:
    # Idempotency: if the same caller already attempted this cancel, return the
    # prior result rather than erroring or re-mutating. This makes rejection
    # retries safe (a failed HTTP does not imply the server did nothing).
    endpoint = "transfers/cancel"
    payload = {"approvalId": approval_id}
    if idempotency_key:
        existing = idempotency.lookup(session, idempotency_key, user_id)
        if existing is not None and existing.endpoint == endpoint:
            idempotency.check_conflict(existing, payload)
            import json

            return json.loads(existing.response_json)

    approval = approval_repository.get_approval_for_user(session, approval_id, user_id)
    if approval is None:
        raise NotFoundError("This approval is no longer available.")
    if approval.status not in PENDING_STATES:
        raise AppError(f"This approval is {approval.status.lower()} and cannot be cancelled.", code=APPROVAL_ALREADY_USED, status=409)

    approval.status = APPROVAL_CANCELLED
    approval.decision_at = now_utc_iso()
    beneficiary = beneficiary_repository.get_beneficiary(session, user_id, approval.beneficiary_id)
    account = account_repository.get_account_by_id(session, approval.source_account_id)
    audit_service.record(session, user_id=user_id, action="transfer.cancel", target=approval.id, request_id=request_id)
    response = _approval_to_dict(approval, beneficiary, account.balance_paise, consumed=True)
    if idempotency_key:
        idempotency.save(
            session,
            key=idempotency_key,
            user_id=user_id,
            endpoint=endpoint,
            payload=payload,
            status_code=200,
            response=response,
        )
    return response


def status(session: Session, *, approval_id: str, user_id: str) -> dict:
    approval = approval_repository.get_approval_for_user(session, approval_id, user_id)
    if approval is None:
        raise NotFoundError("This approval is no longer available.")

    beneficiary = beneficiary_repository.get_beneficiary(session, user_id, approval.beneficiary_id)
    account = account_repository.get_account_by_id(session, approval.source_account_id)
    result: dict = {
        "approval": _approval_to_dict(approval, beneficiary, account.balance_paise, consumed=approval.status not in PENDING_STATES),
    }
    if approval.status == APPROVAL_COMPLETED and approval.transaction_id:
        from app.repositories.transaction_repository import get_transaction

        txn = get_transaction(session, approval.transaction_id)
        if txn:
            result["transaction"] = {
                "id": txn.id,
                "merchant": txn.merchant,
                "category": txn.category,
                "amountPaise": txn.amount_paise,
                "date": txn.occurred_at,
                "status": txn.status,
                "reference": txn.reference,
                "note": txn.note,
            }
            result["updatedBalancePaise"] = account.balance_paise
    return result


def _parse_iso(value: str):
    from datetime import datetime

    return datetime.fromisoformat(value)


def _approval_to_dict(approval: TransferApproval, beneficiary, current_balance_paise: int, *, consumed: bool | None = None) -> dict:
    return {
        "approvalId": approval.id,
        "beneficiary": {
            "id": beneficiary.id,
            "fullName": beneficiary.full_name,
            "alias": beneficiary.alias,
            "dailyLimitPaise": beneficiary.daily_limit_paise,
        },
        "amountPaise": approval.amount_paise,
        "sourceAccountId": approval.source_account_id,
        "currentBalancePaise": current_balance_paise,
        "projectedBalancePaise": current_balance_paise - approval.amount_paise,
        "expiresAt": approval.expires_at,
        "status": approval.status,
        "consumed": bool(consumed if consumed is not None else approval.status not in PENDING_STATES),
        "idempotencyKey": approval.idempotency_key,
    }
