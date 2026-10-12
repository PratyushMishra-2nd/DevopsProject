from datetime import date, timedelta

from tests.conftest import lot_payload

TODAY = date.today()


def days(n: int) -> str:
    return (TODAY + timedelta(days=n)).isoformat()


def test_create_lot_returns_201_and_computes_freshness(client, donor):
    resp = client.post("/api/lots", json=lot_payload(donor_id=donor["id"], expires_on=days(1)))
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] > 0
    assert body["status"] == "available"
    assert body["donor_name"] == "Kalinga Organic Farms"
    assert body["days_left"] == 1
    assert body["freshness"] == "critical"


def test_list_lots_orders_by_expiry_and_filters(client):
    client.post(
        "/api/lots", json=lot_payload(item_name="Rice", category="grains", storage="ambient", expires_on=days(200))
    )
    client.post("/api/lots", json=lot_payload(item_name="Milk", category="dairy", expires_on=days(2)))

    all_lots = client.get("/api/lots").json()
    assert [lot["item_name"] for lot in all_lots] == ["Milk", "Rice"]

    dairy = client.get("/api/lots", params={"category": "dairy"}).json()
    assert [lot["item_name"] for lot in dairy] == ["Milk"]

    soon = client.get("/api/lots", params={"expiring_within": 7}).json()
    assert [lot["item_name"] for lot in soon] == ["Milk"]

    search = client.get("/api/lots", params={"q": "ric"}).json()
    assert [lot["item_name"] for lot in search] == ["Rice"]


def test_get_lot_by_id(client, lot):
    resp = client.get(f"/api/lots/{lot['id']}")
    assert resp.status_code == 200
    assert resp.json()["item_name"] == "Tomatoes"


def test_get_missing_lot_returns_404(client):
    resp = client.get("/api/lots/9999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Stock lot 9999 not found"


def test_create_lot_rejects_invalid_payload(client):
    resp = client.post("/api/lots", json=lot_payload(quantity=-5, category="sweets"))
    assert resp.status_code == 422
    fields = {err["loc"][-1] for err in resp.json()["detail"]}
    assert {"quantity", "category"} <= fields


def test_create_lot_rejects_expiry_before_receipt(client):
    resp = client.post("/api/lots", json=lot_payload(received_on=days(0), expires_on=days(-1)))
    assert resp.status_code == 422


def test_create_lot_rejects_unknown_donor(client):
    resp = client.post("/api/lots", json=lot_payload(donor_id=42))
    assert resp.status_code == 422
    assert resp.json()["detail"] == "Donor 42 does not exist"


def test_update_lot_changes_only_sent_fields(client, lot):
    resp = client.put(
        f"/api/lots/{lot['id']}", json={"quantity": 12.5, "status": "on_hold", "notes": "Check for bruising"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["quantity"] == 12.5
    assert body["status"] == "on_hold"
    assert body["notes"] == "Check for bruising"
    assert body["item_name"] == lot["item_name"]


def test_update_lot_to_zero_marks_depleted(client, lot):
    body = client.put(f"/api/lots/{lot['id']}", json={"quantity": 0}).json()
    assert body["status"] == "depleted"


def test_update_missing_lot_returns_404(client):
    assert client.put("/api/lots/777", json={"quantity": 1}).status_code == 404


def test_update_lot_rejects_null_required_field(client, lot):
    resp = client.put(f"/api/lots/{lot['id']}", json={"item_name": None})
    assert resp.status_code == 422


def test_delete_lot(client, lot):
    assert client.delete(f"/api/lots/{lot['id']}").status_code == 204
    assert client.get(f"/api/lots/{lot['id']}").status_code == 404


def test_delete_missing_lot_returns_404(client):
    assert client.delete("/api/lots/31337").status_code == 404


def test_summary_counts_expiring_and_expired(client):
    client.post("/api/lots", json=lot_payload(item_name="Rice", expires_on=days(90)))
    client.post("/api/lots", json=lot_payload(item_name="Milk", category="dairy", expires_on=days(3)))
    client.post(
        "/api/lots",
        json=lot_payload(item_name="Curd", category="dairy", received_on=days(-5), expires_on=days(-1)),
    )
    body = client.get("/api/lots/summary").json()
    assert body["active_lots"] == 3
    assert body["expiring_soon"] == 1
    assert body["expired_on_shelf"] == 1
    assert body["by_category"] == {"produce": 1, "dairy": 2}
