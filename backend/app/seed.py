"""Load demo data for PantryPulse (idempotent: does nothing if donors already exist).

Usage: python -m app.seed
Dates are relative to today so the expiry dashboard always has something to show.
"""

import logging
from datetime import date, timedelta

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Dispatch, Donor, StockLot

log = logging.getLogger("pantrypulse.seed")

DONORS = [
    ("Mishra Family Grocers", "grocer", "Bhubaneswar", "stock@mishrafamilygrocers.example"),
    ("Kalinga Organic Farms", "farm", "Cuttack", "harvest@kalingaorganic.example"),
    ("Saffron Kitchen Collective", "restaurant", "Bhubaneswar", None),
    ("Mahanadi Dairy Co-op", "manufacturer", "Sambalpur", "dispatch@mahanadidairy.example"),
    ("PantryPulse Neighbourhood Drive", "household", "Puri", None),
]

# item, category, qty, unit, storage, days_since_received, days_to_expiry, donor_index, notes
LOTS = [
    ("Basmati rice, 5 kg bags", "grains", 120, "kg", "ambient", 12, 240, 0, None),
    ("Whole wheat atta", "grains", 80, "kg", "ambient", 6, 120, 0, None),
    ("Toned milk pouches", "dairy", 64, "litres", "chilled", 1, 2, 3, "Cold room shelf C2"),
    ("Paneer blocks", "dairy", 18, "kg", "chilled", 2, 5, 3, None),
    ("Tomatoes", "produce", 45, "kg", "chilled", 1, 4, 1, "Sort out soft ones daily"),
    ("Spinach bunches", "produce", 60, "units", "chilled", 0, 1, 1, None),
    ("Bananas", "produce", 12, "crates", "ambient", 2, 3, 1, None),
    ("Multigrain bread loaves", "bakery", 40, "units", "ambient", 0, 3, 2, None),
    ("Chickpeas, tinned", "canned", 200, "units", "ambient", 30, 400, 0, None),
    ("Frozen mixed vegetables", "produce", 36, "kg", "frozen", 10, 150, 4, None),
    ("Red lentils (masoor dal)", "protein", 95, "kg", "ambient", 8, 300, 4, None),
    ("Curd tubs", "dairy", 22, "kg", "chilled", 3, -1, 3, "Expired: log as discard"),
    ("Orange juice cartons", "beverages", 48, "litres", "ambient", 5, 60, 2, None),
    ("Eggs, trays of 30", "protein", 15, "crates", "chilled", 2, 12, 1, None),
]

DISPATCHES = [
    (0, "Asha Night Shelter", 20, 2),
    (1, "Sunrise Primary School Kitchen", 15, 1),
    (2, "Asha Night Shelter", 10, 0),
    (8, "Old Town Community Kitchen", 48, 3),
    (10, "Sunrise Primary School Kitchen", 12, 5),
]


def seed() -> bool:
    today = date.today()
    with SessionLocal() as db:
        if db.scalar(select(Donor.id).limit(1)) is not None:
            log.info("seed skipped: data already present")
            return False
        donors = [Donor(name=n, kind=k, city=c, contact_email=e) for n, k, c, e in DONORS]
        db.add_all(donors)
        db.flush()
        lots = []
        for item, cat, qty, unit, storage, since, to_expiry, donor_idx, notes in LOTS:
            lots.append(
                StockLot(
                    item_name=item,
                    category=cat,
                    quantity=qty,
                    unit=unit,
                    storage=storage,
                    status="available",
                    received_on=today - timedelta(days=since),
                    expires_on=today + timedelta(days=to_expiry),
                    donor_id=donors[donor_idx].id,
                    notes=notes,
                )
            )
        db.add_all(lots)
        db.flush()
        for lot_idx, partner, qty, days_ago in DISPATCHES:
            lot = lots[lot_idx]
            lot.quantity -= qty
            db.add(
                Dispatch(lot_id=lot.id, partner=partner, quantity=qty, dispatched_on=today - timedelta(days=days_ago))
            )
        db.commit()
        log.info("seed complete", extra={"donors": len(donors), "lots": len(lots), "dispatches": len(DISPATCHES)})
        return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed()
