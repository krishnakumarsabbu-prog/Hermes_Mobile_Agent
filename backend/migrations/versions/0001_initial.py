"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-24 00:00:00
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("profile", sa.String(60), nullable=False, server_default="default"),
    )

    op.create_table(
        "accounts",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("masked_number", sa.String(20), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("balance_paise", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("opening_balance_paise", sa.BigInteger, nullable=False, server_default="0"),
        sa.CheckConstraint("balance_paise >= 0", name="ck_accounts_balance_nonnegative"),
    )
    op.create_index("ix_accounts_user_id", "accounts", ["user_id"])

    op.create_table(
        "beneficiaries",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("alias", sa.String(60), nullable=False),
        sa.Column("account_number_masked", sa.String(30), nullable=False, server_default="••••"),
        sa.Column("daily_limit_paise", sa.BigInteger, nullable=False, server_default="10000000"),
        sa.CheckConstraint("daily_limit_paise >= 0", name="ck_beneficiary_daily_limit_nonnegative"),
    )
    op.create_index("ix_beneficiaries_user_id", "beneficiaries", ["user_id"])

    op.create_table(
        "transfer_approvals",
        sa.Column("id", sa.String(48), primary_key=True),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_account_id", sa.String(32), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("beneficiary_id", sa.String(40), sa.ForeignKey("beneficiaries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount_paise", sa.BigInteger, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("status", sa.String(24), nullable=False, server_default="WAITING_FOR_APPROVAL"),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.Column("expires_at", sa.String(40), nullable=False),
        sa.Column("decision_at", sa.String(40), nullable=True),
        sa.Column("idempotency_key", sa.String(120), nullable=False),
        sa.Column("transaction_id", sa.String(48), sa.ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("version", sa.BigInteger, nullable=False, server_default="1"),
        sa.CheckConstraint("amount_paise > 0", name="ck_approval_amount_positive"),
    )
    op.create_index("ix_approval_user_status", "transfer_approvals", ["user_id", "status"])
    op.create_index("ix_approval_idem", "transfer_approvals", ["idempotency_key"])

    op.create_table(
        "transactions",
        sa.Column("id", sa.String(48), primary_key=True),
        sa.Column("account_id", sa.String(32), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("merchant", sa.String(140), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("amount_paise", sa.BigInteger, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="successful"),
        sa.Column("reference", sa.String(48), nullable=False, unique=True),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("occurred_at", sa.String(40), nullable=False),
        sa.Column("approval_id", sa.String(48), sa.ForeignKey("transfer_approvals.id", ondelete="SET NULL"), nullable=True),
        sa.CheckConstraint("amount_paise > 0", name="ck_transactions_amount_positive"),
    )
    op.create_index("ix_transactions_account_occurred", "transactions", ["account_id", "occurred_at"])
    op.create_index("ix_transactions_category", "transactions", ["category"])
    op.create_index("ix_transactions_status", "transactions", ["status"])

    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.String(48), primary_key=True),
        sa.Column("account_id", sa.String(32), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("approval_id", sa.String(48), sa.ForeignKey("transfer_approvals.id", ondelete="CASCADE"), nullable=True),
        sa.Column("transaction_id", sa.String(48), sa.ForeignKey("transactions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("entry_type", sa.String(8), nullable=False),
        sa.Column("amount_paise", sa.BigInteger, nullable=False),
        sa.Column("reference", sa.String(48), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.CheckConstraint("amount_paise > 0", name="ck_ledger_amount_positive"),
    )
    op.create_index("ix_ledger_account", "ledger_entries", ["account_id"])
    op.create_index("ix_ledger_approval", "ledger_entries", ["approval_id"])

    op.create_table(
        "conversations",
        sa.Column("id", sa.String(48), primary_key=True),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(120), nullable=False, server_default="Conversation"),
        sa.Column("created_at", sa.String(40), nullable=False),
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])

    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.String(48), primary_key=True),
        sa.Column("conversation_id", sa.String(48), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("response_json", sa.Text, nullable=True),
        sa.Column("created_at", sa.String(40), nullable=False),
    )
    op.create_index("ix_convmsg_conversation", "conversation_messages", ["conversation_id"])

    op.create_table(
        "assistant_executions",
        sa.Column("id", sa.String(48), primary_key=True),
        sa.Column("conversation_id", sa.String(48), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message_id", sa.String(48), sa.ForeignKey("conversation_messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("intent", sa.String(60), nullable=False),
        sa.Column("tool", sa.String(60), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ok"),
        sa.Column("detail", sa.Text, nullable=True),
        sa.Column("created_at", sa.String(40), nullable=False),
    )

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(48), primary_key=True),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(60), nullable=False),
        sa.Column("target", sa.String(60), nullable=True),
        sa.Column("detail", sa.Text, nullable=True),
        sa.Column("request_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.String(40), nullable=False),
    )
    op.create_index("ix_audit_user_action", "audit_events", ["user_id", "action"])
    op.create_index("ix_audit_request_id", "audit_events", ["request_id"])

    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.String(48), primary_key=True),
        sa.Column("key", sa.String(120), nullable=False),
        sa.Column("user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("endpoint", sa.String(80), nullable=False),
        sa.Column("payload_hash", sa.String(128), nullable=False),
        sa.Column("status_code", sa.String(8), nullable=False),
        sa.Column("response_json", sa.Text, nullable=True),
        sa.Column("created_at", sa.String(40), nullable=False),
    )
    op.create_index("ix_idem_key_user", "idempotency_records", ["key", "user_id"])


def downgrade() -> None:
    op.drop_table("idempotency_records")
    op.drop_table("audit_events")
    op.drop_table("assistant_executions")
    op.drop_table("conversation_messages")
    op.drop_table("conversations")
    op.drop_table("ledger_entries")
    op.drop_table("transactions")
    op.drop_table("transfer_approvals")
    op.drop_table("beneficiaries")
    op.drop_table("accounts")
    op.drop_table("users")
