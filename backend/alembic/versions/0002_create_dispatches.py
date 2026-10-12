"""create dispatches table

Revision ID: 0002_dispatches
Revises: 0001_donors_lots
Create Date: 2026-10-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_dispatches"
down_revision: str | None = "0001_donors_lots"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dispatches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lot_id", sa.Integer(), sa.ForeignKey("stock_lots.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("partner", sa.String(120), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("dispatched_on", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_dispatches_quantity_positive"),
    )
    op.create_index("ix_dispatches_lot_id", "dispatches", ["lot_id"])


def downgrade() -> None:
    op.drop_table("dispatches")
