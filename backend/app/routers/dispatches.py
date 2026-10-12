from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.metrics import DISPATCHED_QUANTITY
from app.models import Dispatch, StockLot
from app.schemas import DispatchCreate, DispatchRead, ErrorResponse, LotStatus

router = APIRouter(prefix="/api/dispatches", tags=["dispatches"])


def _read(d: Dispatch) -> DispatchRead:
    return DispatchRead(
        id=d.id,
        lot_id=d.lot_id,
        item_name=d.lot.item_name,
        unit=d.lot.unit,
        partner=d.partner,
        quantity=d.quantity,
        dispatched_on=d.dispatched_on,
        created_at=d.created_at,
    )


@router.get("", response_model=list[DispatchRead])
def list_dispatches(lot_id: int | None = None, db: Session = Depends(get_db)) -> list[DispatchRead]:
    stmt = (
        select(Dispatch).options(selectinload(Dispatch.lot)).order_by(Dispatch.dispatched_on.desc(), Dispatch.id.desc())
    )
    if lot_id is not None:
        stmt = stmt.where(Dispatch.lot_id == lot_id)
    return [_read(d) for d in db.scalars(stmt).all()]


@router.post(
    "",
    response_model=DispatchRead,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def create_dispatch(payload: DispatchCreate, db: Session = Depends(get_db)) -> DispatchRead:
    lot = db.get(StockLot, payload.lot_id, with_for_update=True)
    if lot is None:
        raise HTTPException(status_code=404, detail=f"Stock lot {payload.lot_id} not found")
    if lot.status != LotStatus.available.value:
        raise HTTPException(status_code=409, detail=f"Lot is {lot.status.replace('_', ' ')} and cannot be dispatched")
    if lot.expires_on < date.today():
        raise HTTPException(status_code=409, detail="Lot has expired; food safety rules block dispatch")
    if payload.quantity > lot.quantity:
        raise HTTPException(
            status_code=422,
            detail=f"Only {lot.quantity:g} {lot.unit} left in this lot",
        )

    lot.quantity = round(lot.quantity - payload.quantity, 3)
    if lot.quantity == 0:
        lot.status = LotStatus.depleted.value
    dispatch = Dispatch(
        lot_id=lot.id,
        partner=payload.partner,
        quantity=payload.quantity,
        dispatched_on=payload.dispatched_on or date.today(),
    )
    db.add(dispatch)
    db.commit()
    DISPATCHED_QUANTITY.labels(category=lot.category, unit=lot.unit).inc(payload.quantity)
    db.refresh(dispatch)
    return _read(dispatch)


@router.delete("/{dispatch_id}", status_code=status.HTTP_204_NO_CONTENT, responses={404: {"model": ErrorResponse}})
def void_dispatch(dispatch_id: int, db: Session = Depends(get_db)) -> Response:
    """Void a dispatch recorded by mistake: the quantity goes back on the shelf."""
    dispatch = db.get(Dispatch, dispatch_id)
    if dispatch is None:
        raise HTTPException(status_code=404, detail=f"Dispatch {dispatch_id} not found")
    lot = dispatch.lot
    lot.quantity = round(lot.quantity + dispatch.quantity, 3)
    if lot.status == LotStatus.depleted.value:
        lot.status = LotStatus.available.value
    db.delete(dispatch)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
