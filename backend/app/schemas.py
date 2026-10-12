from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class Category(StrEnum):
    produce = "produce"
    dairy = "dairy"
    bakery = "bakery"
    grains = "grains"
    canned = "canned"
    protein = "protein"
    beverages = "beverages"


class Unit(StrEnum):
    kg = "kg"
    litres = "litres"
    units = "units"
    crates = "crates"


class Storage(StrEnum):
    ambient = "ambient"
    chilled = "chilled"
    frozen = "frozen"


class LotStatus(StrEnum):
    available = "available"
    on_hold = "on_hold"
    depleted = "depleted"
    discarded = "discarded"


class DonorKind(StrEnum):
    grocer = "grocer"
    farm = "farm"
    restaurant = "restaurant"
    manufacturer = "manufacturer"
    household = "household"


class Freshness(StrEnum):
    expired = "expired"
    critical = "critical"  # 0-2 days left
    soon = "soon"  # within the warning window
    fresh = "fresh"


def _strip(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


# ---------- donors ----------


class DonorBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    kind: DonorKind
    city: str = Field(min_length=2, max_length=80)
    contact_email: EmailStr | None = None

    @field_validator("name", "city")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("must contain at least 2 non-space characters")
        return v


class DonorCreate(DonorBase):
    pass


class DonorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    kind: DonorKind | None = None
    city: str | None = Field(default=None, min_length=2, max_length=80)
    contact_email: EmailStr | None = None


class DonorRead(DonorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    lot_count: int = 0


# ---------- stock lots ----------


class LotBase(BaseModel):
    item_name: str = Field(min_length=2, max_length=120)
    category: Category
    quantity: float = Field(ge=0, le=100_000)
    unit: Unit
    storage: Storage
    received_on: date
    expires_on: date
    notes: str | None = Field(default=None, max_length=500)
    donor_id: int | None = None

    @field_validator("item_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("must contain at least 2 non-space characters")
        return v

    @field_validator("notes")
    @classmethod
    def clean_notes(cls, v: str | None) -> str | None:
        return _strip(v)


class LotCreate(LotBase):
    quantity: float = Field(gt=0, le=100_000)

    @model_validator(mode="after")
    def expiry_after_receipt(self) -> "LotCreate":
        if self.expires_on < self.received_on:
            raise ValueError("expires_on cannot be before received_on")
        return self


class LotUpdate(BaseModel):
    """All fields optional: PUT updates only what is sent."""

    item_name: str | None = Field(default=None, min_length=2, max_length=120)
    category: Category | None = None
    quantity: float | None = Field(default=None, ge=0, le=100_000)
    unit: Unit | None = None
    storage: Storage | None = None
    status: LotStatus | None = None
    received_on: date | None = None
    expires_on: date | None = None
    notes: str | None = Field(default=None, max_length=500)
    donor_id: int | None = None


class LotRead(LotBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: LotStatus
    donor_name: str | None = None
    days_left: int
    freshness: Freshness
    created_at: datetime
    updated_at: datetime


class LotSummary(BaseModel):
    active_lots: int
    expiring_soon: int
    expired_on_shelf: int
    dispatched_this_week: float
    partners_served: int
    by_category: dict[str, int]
    by_storage: dict[str, int]
    warning_days: int


# ---------- dispatches ----------


class DispatchCreate(BaseModel):
    lot_id: int
    partner: str = Field(min_length=2, max_length=120)
    quantity: float = Field(gt=0, le=100_000)
    dispatched_on: date | None = None

    @field_validator("partner")
    @classmethod
    def clean_partner(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("must contain at least 2 non-space characters")
        return v


class DispatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lot_id: int
    item_name: str
    unit: str
    partner: str
    quantity: float
    dispatched_on: date
    created_at: datetime


class ErrorResponse(BaseModel):
    detail: str
