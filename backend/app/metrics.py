"""Business metrics exported next to the HTTP metrics on /metrics."""

from prometheus_client import Counter

LOTS_CREATED = Counter(
    "pantrypulse_lots_created_total",
    "Stock lots received into the pantry",
    ["category"],
)

DISPATCHED_QUANTITY = Counter(
    "pantrypulse_dispatched_quantity_total",
    "Quantity of food dispatched to partner organisations",
    ["category", "unit"],
)
