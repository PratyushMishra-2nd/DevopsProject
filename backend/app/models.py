from datetime import UTC, date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Donor(Base):
    """A business or person that gives food to the pantry."""

    __tablename__ = "donors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    lots: Mapped[list["StockLot"]] = relationship(back_populates="donor")


class StockLot(Base):
    """One batch of a food item on the shelves, with its own expiry date."""

    __tablename__ = "stock_lots"
    __table_args__ = (CheckConstraint("quantity >= 0", name="ck_stock_lots_quantity_non_negative"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(10), nullable=False)
    storage: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="available", index=True)
    received_on: Mapped[date] = mapped_column(Date, nullable=False)
    expires_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    donor_id: Mapped[int | None] = mapped_column(ForeignKey("donors.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    donor: Mapped[Donor | None] = relationship(back_populates="lots")
    dispatches: Mapped[list["Dispatch"]] = relationship(back_populates="lot")


class Dispatch(Base):
    """Food handed out from a lot to a partner organisation (shelter, school, kitchen)."""

    __tablename__ = "dispatches"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_dispatches_quantity_positive"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lot_id: Mapped[int] = mapped_column(ForeignKey("stock_lots.id", ondelete="RESTRICT"), nullable=False, index=True)
    partner: Mapped[str] = mapped_column(String(120), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    dispatched_on: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    lot: Mapped[StockLot] = relationship(back_populates="dispatches")
