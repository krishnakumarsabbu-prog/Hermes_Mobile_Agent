"""Deterministic synthetic data generator.

Produces an internally consistent dataset:
- The demo user usr_01 / acct_01 with the canonical current-month transactions.
- Many synthetic users with accounts, beneficiaries, transactions and a sample
  of historical successful transfers with matching ledger rows.

The demo user's current-month spending is EXACTLY the four canonical
transactions (₹32,500 total). Additional demo-user records are only generated
for prior months so they never contaminate the canonical current-month test.

All randomness is deterministic via a fixed seed. Inserts are batched so we
never hold 100k rows in a single unbounded list at once.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Iterator

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.account import Account, User
from app.models.approval import TransferApproval, APPROVAL_COMPLETED, APPROVAL_WAITING
from app.models.audit import AuditEvent
from app.models.beneficiary import Beneficiary
from app.models.ledger import LedgerEntry, ENTRY_DEBIT
from app.models.transaction import Transaction, STATUS_SUCCESSFUL, CATEGORY_DINING, CATEGORY_SHOPPING, CATEGORY_UTILITY, CATEGORY_TRANSFER

KOLKATA = ZoneInfo("Asia/Kolkata")
DEMO_USER_ID = "usr_01"
DEMO_ACCOUNT_ID = "acct_01"
DEMO_BENEFICIARY_ID = "ben_ravi"

MERCHANTS = [
    ("Trattoria", CATEGORY_DINING, (50000, 500000)),
    ("Brew Room", CATEGORY_DINING, (30000, 400000)),
    ("The Coffee House", CATEGORY_DINING, (20000, 250000)),
    ("Shopping Store", CATEGORY_SHOPPING, (100000, 2000000)),
    ("Mega Mart", CATEGORY_SHOPPING, (50000, 1500000)),
    ("Electricity Provider", CATEGORY_UTILITY, (300000, 900000)),
    ("Water Board", CATEGORY_UTILITY, (100000, 400000)),
    ("Broadband Co", CATEGORY_UTILITY, (80000, 300000)),
]
BENEFICIARY_NAMES = [
    "Ravi Sharma", "Priya Patel", "Arjun Nair", "Sneha Reddy", "Vikram Singh",
    "Anita Gupta", "Rohit Mehta", "Kavya Iyer", "Sanjay Rao", "Pooja Joshi",
]


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _current_month_start_local() -> datetime:
    now = datetime.now(KOLKATA)
    return datetime(now.year, now.month, 1, tzinfo=KOLKATA)


def _utc_iso_from_local(local_dt: datetime) -> str:
    return local_dt.astimezone(timezone.utc).isoformat()


def generate(session: Session, *, reset: bool = False) -> dict:
    """Generate and persist the full dataset. Idempotent: if demo data already
    exists and reset is False, this is a no-op for the demo user.
    """
    settings = get_settings()
    rng = random.Random(20261024)

    if reset:
        _truncate_all(session)

    # Demo user.
    _seed_demo(session, settings, rng)

    # Synthetic users (skip if already present to keep seeding idempotent).
    existing = session.query(User).count()
    if existing <= 1:
        _seed_synthetic(session, settings, rng)

    session.commit()
    counts = {
        "users": session.query(User).count(),
        "accounts": session.query(Account).count(),
        "beneficiaries": session.query(Beneficiary).count(),
        "transactions": session.query(Transaction).count(),
        "transfer_approvals": session.query(TransferApproval).count(),
        "ledger_entries": session.query(LedgerEntry).count(),
        "audit_events": session.query(AuditEvent).count(),
    }
    return counts


def _truncate_all(session: Session) -> None:
    for table in [
        "ledger_entries", "transactions", "transfer_approvals", "audit_events",
        "idempotency_records", "assistant_executions", "conversation_messages",
        "conversations", "beneficiaries", "accounts", "users",
    ]:
        session.execute(_text(f"DELETE FROM {table}"))
    session.commit()


def _text(sql: str):
    from sqlalchemy import text

    return text(sql)


def _seed_demo(session: Session, settings, rng: random.Random) -> None:
    if session.get(User, DEMO_USER_ID) is not None:
        return

    user = User(id=DEMO_USER_ID, display_name="Alex Hermes", profile="hermes_bank_01")
    session.add(user)

    account = Account(
        id=DEMO_ACCOUNT_ID,
        user_id=DEMO_USER_ID,
        name="Everyday Checking",
        masked_number="•••• 0987",
        currency="INR",
        balance_paise=10000000,  # ₹1,00,000
        opening_balance_paise=10000000,
    )
    session.add(account)

    ravi = Beneficiary(
        id=DEMO_BENEFICIARY_ID,
        user_id=DEMO_USER_ID,
        full_name="Ravi Sharma",
        alias="Ravi",
        account_number_masked="•••• 4521",
        daily_limit_paise=10000000,
    )
    session.add(ravi)
    # A second demo beneficiary for ambiguity-free tests.
    session.add(Beneficiary(
        id="ben_priya",
        user_id=DEMO_USER_ID,
        full_name="Priya Patel",
        alias="Priya",
        account_number_masked="•••• 7788",
        daily_limit_paise=10000000,
    ))
    session.flush()

    # Canonical current-month transactions (in reporting tz noon).
    now_local = datetime.now(KOLKATA)
    canonical = [
        ("txn_trattoria", "Trattoria", CATEGORY_DINING, 320000, 3, "HMS-DEMO-TRAT"),
        ("txn_brew", "Brew Room", CATEGORY_DINING, 300000, 7, "HMS-DEMO-BREW"),
        ("txn_shopping", "Shopping Store", CATEGORY_SHOPPING, 1800000, 12, "HMS-DEMO-SHOP"),
        ("txn_electricity", "Electricity Provider", CATEGORY_UTILITY, 830000, 16, "HMS-DEMO-UTIL"),
    ]
    for tid, merchant, cat, amount, day, ref in canonical:
        local = datetime(now_local.year, now_local.month, day, 12, 0, tzinfo=KOLKATA)
        session.add(Transaction(
            id=tid,
            account_id=DEMO_ACCOUNT_ID,
            merchant=merchant,
            category=cat,
            amount_paise=amount,
            status=STATUS_SUCCESSFUL,
            reference=ref,
            occurred_at=_utc_iso_from_local(local),
        ))

    # A few prior-month demo transactions (do NOT affect current-month totals).
    prev_month_start = _current_month_start_local() - timedelta(days=1)
    prev_month_start = datetime(prev_month_start.year, prev_month_start.month, 1, tzinfo=KOLKATA)
    for i in range(3):
        local = prev_month_start + timedelta(days=5 + i * 6, hours=12)
        merchant, cat, (lo, hi) = MERCHANTS[i % len(MERCHANTS)]
        session.add(Transaction(
            id=f"txn_demo_prev_{i}",
            account_id=DEMO_ACCOUNT_ID,
            merchant=merchant,
            category=cat,
            amount_paise=rng.randint(lo, hi),
            status=STATUS_SUCCESSFUL,
            reference=f"HMS-DEMO-PREV-{i}",
            occurred_at=_utc_iso_from_local(local),
        ))

    # One prior-month completed transfer for the demo user with ledger entry.
    prior_transfer_local = prev_month_start + timedelta(days=10, hours=14)
    prior_amount = 5000000  # ₹50,000
    prior_ref = "HMS-DEMO-PREVTFR"
    prior_txn_id = "txn_demo_prev_tfr"
    prior_approval_id = "appr_demo_prev"
    # Insert the transaction first, then the approval that references it.
    session.add(Transaction(
        id=prior_txn_id,
        account_id=DEMO_ACCOUNT_ID,
        merchant="Ravi Sharma",
        category=CATEGORY_TRANSFER,
        amount_paise=prior_amount,
        status=STATUS_SUCCESSFUL,
        reference=prior_ref,
        note="Simulated transfer",
        occurred_at=_utc_iso_from_local(prior_transfer_local),
    ))
    session.flush()
    session.add(TransferApproval(
        id=prior_approval_id,
        user_id=DEMO_USER_ID,
        source_account_id=DEMO_ACCOUNT_ID,
        beneficiary_id=DEMO_BENEFICIARY_ID,
        amount_paise=prior_amount,
        currency="INR",
        status=APPROVAL_COMPLETED,
        created_at=_utc_iso_from_local(prior_transfer_local),
        expires_at=_utc_iso_from_local(prior_transfer_local + timedelta(seconds=300)),
        decision_at=_utc_iso_from_local(prior_transfer_local),
        idempotency_key="seed-demo-prev-tfr",
        transaction_id=prior_txn_id,
        version=2,
    ))
    session.flush()
    session.add(LedgerEntry(
        id="led_demo_prev",
        account_id=DEMO_ACCOUNT_ID,
        approval_id=prior_approval_id,
        transaction_id=prior_txn_id,
        entry_type=ENTRY_DEBIT,
        amount_paise=prior_amount,
        reference=prior_ref,
        created_at=_utc_iso_from_local(prior_transfer_local),
    ))

    session.commit()


def _seed_synthetic(session: Session, settings, rng: random.Random) -> None:
    """Generate the large synthetic dataset in batches."""
    batch = 500
    now = _now_utc()

    # Users + accounts.
    users_batch: list[User] = []
    accounts_batch: list[Account] = []
    beneficiaries_batch: list[Beneficiary] = []
    n_users = settings.seed_users
    n_accounts = settings.seed_accounts_min
    accounts_target = rng.randint(settings.seed_accounts_min, settings.seed_accounts_max)

    for i in range(1, n_users + 1):
        uid = f"synu_{i:05d}"
        users_batch.append(User(id=uid, display_name=f"Synthetic User {i}", profile="synthetic"))
        if i % batch == 0 or i == n_users:
            session.bulk_save_objects(users_batch)
            session.commit()
            users_batch = []

    # Accounts: one per user minimum, extra distributed to reach target.
    account_idx = 0
    for i in range(1, n_users + 1):
        uid = f"synu_{i:05d}"
        account_idx += 1
        opening = rng.randint(1000000, 200000000)
        accounts_batch.append(Account(
            id=f"syna_{account_idx:06d}",
            user_id=uid,
            name="Checking",
            masked_number=f"•••• {rng.randint(1000,9999)}",
            currency="INR",
            balance_paise=opening,
            opening_balance_paise=opening,
        ))
        if len(accounts_batch) >= batch:
            session.bulk_save_objects(accounts_batch)
            session.commit()
            accounts_batch = []
    # Extra accounts to reach target.
    while account_idx < accounts_target:
        account_idx += 1
        uid = f"synu_{rng.randint(1, n_users):05d}"
        opening = rng.randint(1000000, 200000000)
        accounts_batch.append(Account(
            id=f"syna_{account_idx:06d}",
            user_id=uid,
            name="Savings",
            masked_number=f"•••• {rng.randint(1000,9999)}",
            currency="INR",
            balance_paise=opening,
            opening_balance_paise=opening,
        ))
        if len(accounts_batch) >= batch:
            session.bulk_save_objects(accounts_batch)
            session.commit()
            accounts_batch = []
    if accounts_batch:
        session.bulk_save_objects(accounts_batch)
        session.commit()

    # Beneficiaries.
    n_ben = settings.seed_beneficiaries
    for i in range(1, n_ben + 1):
        uid = f"synu_{rng.randint(1, n_users):05d}"
        name = BENEFICIARY_NAMES[i % len(BENEFICIARY_NAMES)]
        alias = name.split()[0]
        beneficiaries_batch.append(Beneficiary(
            id=f"synb_{i:06d}",
            user_id=uid,
            full_name=f"{name} {i}",
            alias=alias,
            account_number_masked=f"•••• {rng.randint(1000,9999)}",
            daily_limit_paise=10000000,
        ))
        if len(beneficiaries_batch) >= batch:
            session.bulk_save_objects(beneficiaries_batch)
            session.commit()
            beneficiaries_batch = []
    if beneficiaries_batch:
        session.bulk_save_objects(beneficiaries_batch)
        session.commit()

    # Transactions: distribute across accounts, last ~18 months.
    n_txn = settings.seed_transactions
    txn_batch: list[Transaction] = []
    months_back = 18
    start_local = _current_month_start_local() - timedelta(days=30 * months_back)

    for i in range(1, n_txn + 1):
        acct_id = f"syna_{rng.randint(1, account_idx):06d}"
        merchant, cat, (lo, hi) = MERCHANTS[rng.randrange(len(MERCHANTS))]
        day_offset = rng.randint(0, months_back * 30)
        local = start_local + timedelta(days=day_offset, hours=rng.randint(8, 20), minutes=rng.randint(0, 59))
        if local >= _current_month_start_local():
            # Keep synthetic transactions out of the current month to avoid
            # contaminating any current-month reconciliation assumptions.
            local = start_local + timedelta(days=day_offset // 2)
        amount = rng.randint(lo, hi)
        ref = f"HMS-SYN-{i:07d}"
        txn_batch.append(Transaction(
            id=f"synt_{i:07d}",
            account_id=acct_id,
            merchant=merchant,
            category=cat,
            amount_paise=amount,
            status=STATUS_SUCCESSFUL,
            reference=ref,
            occurred_at=_utc_iso_from_local(local),
        ))
        if len(txn_batch) >= batch:
            session.bulk_save_objects(txn_batch)
            session.commit()
            txn_batch = []
    if txn_batch:
        session.bulk_save_objects(txn_batch)
        session.commit()

    # Historical successful transfers for a sample of synthetic accounts.
    n_transfers = min(3000, account_idx // 3)
    txn_batch2: list[Transaction] = []
    tx_batch: list[TransferApproval] = []
    led_batch: list[LedgerEntry] = []
    for i in range(1, n_transfers + 1):
        acct_id = f"syna_{rng.randint(1, account_idx):06d}"
        uid = None
        acct = session.get(Account, acct_id)
        if acct is None:
            continue
        uid = acct.user_id
        ben_id = f"synb_{rng.randint(1, n_ben):06d}"
        amount = rng.randint(50000, 5000000)
        local = start_local + timedelta(days=rng.randint(0, months_back * 28), hours=rng.randint(8, 20))
        if local >= _current_month_start_local():
            local = start_local + timedelta(days=rng.randint(0, months_back * 15))
        ref = f"HMS-SYNTFR-{i:06d}"
        txn_id = f"syntfr_{i:06d}"
        appr_id = f"synappr_{i:06d}"
        txn_batch2.append(Transaction(
            id=txn_id,
            account_id=acct_id,
            merchant="Transfer",
            category=CATEGORY_TRANSFER,
            amount_paise=amount,
            status=STATUS_SUCCESSFUL,
            reference=ref,
            note="Simulated transfer",
            occurred_at=_utc_iso_from_local(local),
        ))
        tx_batch.append(TransferApproval(
            id=appr_id,
            user_id=uid,
            source_account_id=acct_id,
            beneficiary_id=ben_id,
            amount_paise=amount,
            currency="INR",
            status=APPROVAL_COMPLETED,
            created_at=_utc_iso_from_local(local),
            expires_at=_utc_iso_from_local(local + timedelta(seconds=300)),
            decision_at=_utc_iso_from_local(local),
            idempotency_key=f"seed-syn-{i}",
            transaction_id=txn_id,
            version=2,
        ))
        led_batch.append(LedgerEntry(
            id=f"synled_{i:06d}",
            account_id=acct_id,
            approval_id=appr_id,
            transaction_id=txn_id,
            entry_type=ENTRY_DEBIT,
            amount_paise=amount,
            reference=ref,
            created_at=_utc_iso_from_local(local),
        ))
        if len(txn_batch2) >= batch:
            # Insert transactions first so FK from approvals resolves.
            session.bulk_save_objects(txn_batch2)
            session.commit()
            session.bulk_save_objects(tx_batch)
            session.commit()
            session.bulk_save_objects(led_batch)
            session.commit()
            txn_batch2, tx_batch, led_batch = [], [], []
    if txn_batch2:
        session.bulk_save_objects(txn_batch2)
        session.commit()
        session.bulk_save_objects(tx_batch)
        session.commit()
        session.bulk_save_objects(led_batch)
        session.commit()
