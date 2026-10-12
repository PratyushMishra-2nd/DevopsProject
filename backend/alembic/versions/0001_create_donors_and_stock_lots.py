"""create donors and stock_lots tables

Revision ID: 0001_donors_lots
Revises:
Create Date: 2026-10-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_donors_lots"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "donors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("city", sa.String(80), nullable=False),
        sa.Column("contact_email", sa.String(160)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name", name="uq_donors_name"),
    )
    op.create_table(
        "stock_lots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_name", sa.String(120), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(10), nullable=False),
        sa.Column("storage", sa.String(10), nullable=False),
        sa.Column("status", sa.String(12), nullable=False, server_default="available"),
        sa.Column("received_on", sa.Date(), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("donor_id", sa.Integer(), sa.ForeignKey("donors.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("quantity >= 0", name="ck_stock_lots_quantity_non_negative"),
    )
    op.create_index("ix_stock_lots_category", "stock_lots", ["category"])
    op.create_index("ix_stock_lots_status", "stock_lots", ["status"])
    op.create_index("ix_stock_lots_expires_on", "stock_lots", ["expires_on"])


def downgrade() -> None:
    op.drop_table("stock_lots")
    op.drop_table("donors")
