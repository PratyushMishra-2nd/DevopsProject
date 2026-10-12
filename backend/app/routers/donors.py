from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Donor, StockLot
from app.schemas import DonorCreate, DonorRead, DonorUpdate, ErrorResponse

router = APIRouter(prefix="/api/donors", tags=["donors"])


def _lot_counts(db: Session) -> dict[int, int]:
    rows = db.execute(
        select(StockLot.donor_id, func.count()).where(StockLot.donor_id.is_not(None)).group_by(StockLot.donor_id)
    )
    return dict(rows.all())


def _read(donor: Donor, counts: dict[int, int]) -> DonorRead:
    return DonorRead(
        id=donor.id,
        name=donor.name,
        kind=donor.kind,
        city=donor.city,
        contact_email=donor.contact_email,
        created_at=donor.created_at,
        lot_count=counts.get(donor.id, 0),
    )


def _get_or_404(db: Session, donor_id: int) -> Donor:
    donor = db.get(Donor, donor_id)
    if donor is None:
        raise HTTPException(status_code=404, detail=f"Donor {donor_id} not found")
    return donor


def _commit_unique(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="A donor with this name already exists") from exc


@router.get("", response_model=list[DonorRead])
def list_donors(db: Session = Depends(get_db)) -> list[DonorRead]:
    counts = _lot_counts(db)
    return [_read(d, counts) for d in db.scalars(select(Donor).order_by(Donor.name)).all()]


@router.get("/{donor_id}", response_model=DonorRead, responses={404: {"model": ErrorResponse}})
def get_donor(donor_id: int, db: Session = Depends(get_db)) -> DonorRead:
    return _read(_get_or_404(db, donor_id), _lot_counts(db))


@router.post(
    "", response_model=DonorRead, status_code=status.HTTP_201_CREATED, responses={409: {"model": ErrorResponse}}
)
def create_donor(payload: DonorCreate, db: Session = Depends(get_db)) -> DonorRead:
    donor = Donor(**payload.model_dump(mode="python"))
    db.add(donor)
    _commit_unique(db)
    return _read(donor, {})


@router.put(
    "/{donor_id}",
    response_model=DonorRead,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def update_donor(donor_id: int, payload: DonorUpdate, db: Session = Depends(get_db)) -> DonorRead:
    donor = _get_or_404(db, donor_id)
    for field, value in payload.model_dump(exclude_unset=True, mode="python").items():
        if value is None and field != "contact_email":
            raise HTTPException(status_code=422, detail=f"{field} cannot be null")
        setattr(donor, field, value.strip() if isinstance(value, str) else value)
    _commit_unique(db)
    return _read(donor, _lot_counts(db))


@router.delete("/{donor_id}", status_code=status.HTTP_204_NO_CONTENT, responses={404: {"model": ErrorResponse}})
def delete_donor(donor_id: int, db: Session = Depends(get_db)) -> Response:
    donor = _get_or_404(db, donor_id)
    # Lots keep their history; the FK is ON DELETE SET NULL, done explicitly so SQLite behaves the same.
    for lot in donor.lots:
        lot.donor_id = None
    db.delete(donor)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
