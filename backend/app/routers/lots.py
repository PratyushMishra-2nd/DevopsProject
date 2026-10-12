from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.db import get_db
from app.metrics import LOTS_CREATED
from app.models import Dispatch, Donor, StockLot
from app.schemas import (
    Category,
    ErrorResponse,
    Freshness,
    LotCreate,
    LotRead,
    LotStatus,
    LotSummary,
    LotUpdate,
    Storage,
)

router = APIRouter(prefix="/api/lots", tags=["stock lots"])

ON_SHELF = (LotStatus.available.value, LotStatus.on_hold.value)


def freshness_for(expires_on: date, today: date, warning_days: int) -> tuple[int, Freshness]:
    days_left = (expires_on - today).days
    if days_left < 0:
        return days_left, Freshness.expired
    if days_left <= 2:
        return days_left, Freshness.critical
    if days_left <= warning_days:
        return days_left, Freshness.soon
    return days_left, Freshness.fresh


def to_read(lot: StockLot) -> LotRead:
    days_left, fresh = freshness_for(lot.expires_on, date.today(), get_settings().expiry_warning_days)
    return LotRead(
        id=lot.id,
        item_name=lot.item_name,
        category=lot.category,
        quantity=lot.quantity,
        unit=lot.unit,
        storage=lot.storage,
        status=lot.status,
        received_on=lot.received_on,
        expires_on=lot.expires_on,
        notes=lot.notes,
        donor_id=lot.donor_id,
        donor_name=lot.donor.name if lot.donor else None,
        days_left=days_left,
        freshness=fresh,
        created_at=lot.created_at,
        updated_at=lot.updated_at,
    )


def get_lot_or_404(db: Session, lot_id: int) -> StockLot:
    lot = db.get(StockLot, lot_id, options=[selectinload(StockLot.donor)])
    if lot is None:
        raise HTTPException(status_code=404, detail=f"Stock lot {lot_id} not found")
    return lot


def ensure_donor_exists(db: Session, donor_id: int | None) -> None:
    if donor_id is not None and db.get(Donor, donor_id) is None:
        raise HTTPException(status_code=422, detail=f"Donor {donor_id} does not exist")


@router.get("", response_model=list[LotRead])
def list_lots(
    category: Category | None = None,
    storage: Storage | None = None,
    status_: LotStatus | None = Query(default=None, alias="status"),
    expiring_within: int | None = Query(default=None, ge=0, le=365, description="Only lots expiring within N days"),
    q: str | None = Query(default=None, max_length=60, description="Search item name"),
    db: Session = Depends(get_db),
) -> list[LotRead]:
    stmt = select(StockLot).options(selectinload(StockLot.donor)).order_by(StockLot.expires_on, StockLot.id)
    if category:
        stmt = stmt.where(StockLot.category == category.value)
    if storage:
        stmt = stmt.where(StockLot.storage == storage.value)
    if status_:
        stmt = stmt.where(StockLot.status == status_.value)
    if expiring_within is not None:
        stmt = stmt.where(StockLot.expires_on <= date.today() + timedelta(days=expiring_within))
    if q:
        stmt = stmt.where(StockLot.item_name.ilike(f"%{q.strip()}%"))
    return [to_read(lot) for lot in db.scalars(stmt).all()]


@router.get("/summary", response_model=LotSummary)
def lot_summary(db: Session = Depends(get_db)) -> LotSummary:
    settings = get_settings()
    today = date.today()
    on_shelf = StockLot.status.in_(ON_SHELF)

    active = db.scalar(select(func.count()).select_from(StockLot).where(on_shelf)) or 0
    soon = (
        db.scalar(
            select(func.count())
            .select_from(StockLot)
            .where(on_shelf, StockLot.expires_on >= today)
            .where(StockLot.expires_on <= today + timedelta(days=settings.expiry_warning_days))
        )
        or 0
    )
    expired = db.scalar(select(func.count()).select_from(StockLot).where(on_shelf, StockLot.expires_on < today)) or 0
    week_ago = today - timedelta(days=7)
    dispatched = db.scalar(
        select(func.coalesce(func.sum(Dispatch.quantity), 0)).where(Dispatch.dispatched_on >= week_ago)
    )
    partners = db.scalar(select(func.count(func.distinct(Dispatch.partner)))) or 0

    by_category = dict(
        db.execute(select(StockLot.category, func.count()).where(on_shelf).group_by(StockLot.category)).all()
    )
    by_storage = dict(
        db.execute(select(StockLot.storage, func.count()).where(on_shelf).group_by(StockLot.storage)).all()
    )
    return LotSummary(
        active_lots=active,
        expiring_soon=soon,
        expired_on_shelf=expired,
        dispatched_this_week=float(dispatched or 0),
        partners_served=partners,
        by_category=by_category,
        by_storage=by_storage,
        warning_days=settings.expiry_warning_days,
    )


@router.get("/{lot_id}", response_model=LotRead, responses={404: {"model": ErrorResponse}})
def get_lot(lot_id: int, db: Session = Depends(get_db)) -> LotRead:
    return to_read(get_lot_or_404(db, lot_id))


@router.post("", response_model=LotRead, status_code=status.HTTP_201_CREATED, responses={422: {"model": ErrorResponse}})
def create_lot(payload: LotCreate, db: Session = Depends(get_db)) -> LotRead:
    ensure_donor_exists(db, payload.donor_id)
    lot = StockLot(**payload.model_dump(mode="python"), status=LotStatus.available.value)
    db.add(lot)
    db.commit()
    LOTS_CREATED.labels(category=lot.category).inc()
    return to_read(get_lot_or_404(db, lot.id))


@router.put(
    "/{lot_id}",
    response_model=LotRead,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def update_lot(lot_id: int, payload: LotUpdate, db: Session = Depends(get_db)) -> LotRead:
    lot = get_lot_or_404(db, lot_id)
    changes = payload.model_dump(exclude_unset=True, mode="python")
    if "donor_id" in changes:
        ensure_donor_exists(db, changes["donor_id"])
    nullable = {"notes", "donor_id"}
    for field, value in changes.items():
        if value is None and field not in nullable:
            raise HTTPException(status_code=422, detail=f"{field} cannot be null")
    # Validate the resulting dates before touching the ORM object.
    if changes.get("expires_on", lot.expires_on) < changes.get("received_on", lot.received_on):
        raise HTTPException(status_code=422, detail="expires_on cannot be before received_on")
    for field, value in changes.items():
        setattr(lot, field, value.strip() if isinstance(value, str) else value)
    if lot.quantity == 0 and lot.status == LotStatus.available.value:
        lot.status = LotStatus.depleted.value
    db.commit()
    return to_read(get_lot_or_404(db, lot_id))


@router.delete(
    "/{lot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def delete_lot(lot_id: int, db: Session = Depends(get_db)) -> Response:
    lot = get_lot_or_404(db, lot_id)
    has_dispatches = db.scalar(select(func.count()).select_from(Dispatch).where(Dispatch.lot_id == lot_id))
    if has_dispatches:
        raise HTTPException(
            status_code=409,
            detail="Lot has dispatch history; mark it discarded instead of deleting it",
        )
    db.delete(lot)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
