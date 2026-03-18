"""initial schema

Revision ID: 5d07dacb94a0
Revises:
Create Date: 2026-03-18 22:42:17.833609

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "5d07dacb94a0"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cognito_sub", sa.String(128), unique=True, nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("email", sa.String(320), unique=True, nullable=False),
        sa.Column("phone", sa.String(20), unique=True, nullable=False),
        sa.Column("company_name", sa.String(512), nullable=False),
        sa.Column("gstin", sa.String(15), nullable=False),
        sa.Column("wallet_address", sa.String(58), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_users_cognito_sub", "users", ["cognito_sub"])
    op.create_index("ix_users_gstin", "users", ["gstin"])

    # --- invoices ---
    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("invoice_number", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="uploaded"),
        sa.Column("file_key", sa.String(512), nullable=False),
        sa.Column("file_name", sa.String(256), nullable=False),
        # AI pipeline JSONB columns
        sa.Column("extracted_data", postgresql.JSONB, nullable=True),
        sa.Column("validation_result", postgresql.JSONB, nullable=True),
        sa.Column("gst_compliance", postgresql.JSONB, nullable=True),
        sa.Column("fraud_detection", postgresql.JSONB, nullable=True),
        sa.Column("gstin_verification", postgresql.JSONB, nullable=True),
        sa.Column("buyer_intel", postgresql.JSONB, nullable=True),
        sa.Column("credit_score", postgresql.JSONB, nullable=True),
        sa.Column("company_info", postgresql.JSONB, nullable=True),
        sa.Column("risk_assessment", postgresql.JSONB, nullable=True),
        sa.Column("underwriting", postgresql.JSONB, nullable=True),
        # Denormalized fields
        sa.Column("risk_score", sa.Integer, nullable=True),
        sa.Column("ai_explanation", sa.Text, nullable=True),
        # Processing timestamps
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_duration_ms", sa.Integer, nullable=True),
        # Standard timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_invoices_user_id", "invoices", ["user_id"])
    op.create_index("ix_invoices_status", "invoices", ["status"])

    # --- rules ---
    op.create_table(
        "rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("conditions", postgresql.JSONB, nullable=False),
        sa.Column(
            "action", sa.String(32), nullable=False, server_default="auto_approve"
        ),
        sa.Column(
            "is_active", sa.Boolean, nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_rules_user_id", "rules", ["user_id"])

    # --- user_settings ---
    op.create_table(
        "user_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            unique=True,
            nullable=False,
        ),
        sa.Column(
            "default_action",
            sa.String(32),
            nullable=False,
            server_default="flag_for_review",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # --- nft_records ---
    op.create_table(
        "nft_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "invoice_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("invoices.id"),
            unique=True,
            nullable=False,
        ),
        sa.Column("asset_id", sa.BigInteger, nullable=True),
        sa.Column("mint_txn_id", sa.String(64), nullable=True),
        sa.Column("opt_in_txn_id", sa.String(64), nullable=True),
        sa.Column("transfer_txn_id", sa.String(64), nullable=True),
        sa.Column("claimed_by_wallet", sa.String(58), nullable=True),
        sa.Column("arc69_metadata", postgresql.JSONB, nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="minted"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # --- agent_traces ---
    op.create_table(
        "agent_traces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "invoice_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("invoices.id"),
            nullable=False,
        ),
        sa.Column("agent_name", sa.String(64), nullable=False),
        sa.Column("model", sa.String(64), nullable=False),
        sa.Column("duration_ms", sa.Integer, nullable=False),
        sa.Column("steps", postgresql.JSONB, nullable=False),
        sa.Column("handoff_context", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_agent_traces_invoice_id", "agent_traces", ["invoice_id"])


def downgrade() -> None:
    op.drop_table("agent_traces")
    op.drop_table("nft_records")
    op.drop_table("user_settings")
    op.drop_table("rules")
    op.drop_table("invoices")
    op.drop_table("users")
