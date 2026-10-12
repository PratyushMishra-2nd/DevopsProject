from datetime import date, timedelta

from tests.conftest import lot_payload


def test_dispatch_reduces_lot_quantity(client, lot):
    resp = client.post("/api/dispatches", json={"lot_id": lot["id"], "partner": "Asha Night Shelter", "quantity": 15})
    assert resp.status_code == 201
    assert resp.json()["item_name"] == "Tomatoes"
    assert client.get(f"/api/lots/{lot['id']}").json()["quantity"] == 25


def test_dispatch_entire_lot_marks_it_depleted(client, lot):
    client.post("/api/dispatches", json={"lot_id": lot["id"], "partner": "Asha Night Shelter", "quantity": 40})
    assert client.get(f"/api/lots/{lot['id']}").json()["status"] == "depleted"


def test_dispatch_more_than_available_is_rejected(client, lot):
    resp = client.post("/api/dispatches", json={"lot_id": lot["id"], "partner": "School kitchen", "quantity": 41})
    assert resp.status_code == 422
    assert resp.json()["detail"] == "Only 40 kg left in this lot"


def test_dispatch_from_expired_lot_is_blocked(client):
    today = date.today()
    expired = client.post(
        "/api/lots",
        json=lot_payload(
            received_on=(today - timedelta(days=4)).isoformat(), expires_on=(today - timedelta(days=1)).isoformat()
        ),
    ).json()
    resp = client.post("/api/dispatches", json={"lot_id": expired["id"], "partner": "Shelter", "quantity": 1})
    assert resp.status_code == 409


def test_dispatch_from_lot_on_hold_is_blocked(client, lot):
    client.put(f"/api/lots/{lot['id']}", json={"status": "on_hold"})
    resp = client.post("/api/dispatches", json={"lot_id": lot["id"], "partner": "Shelter", "quantity": 1})
    assert resp.status_code == 409


def test_dispatch_for_missing_lot_returns_404(client):
    resp = client.post("/api/dispatches", json={"lot_id": 999, "partner": "Shelter", "quantity": 1})
    assert resp.status_code == 404


def test_lot_with_dispatch_history_cannot_be_deleted(client, lot):
    client.post("/api/dispatches", json={"lot_id": lot["id"], "partner": "Shelter", "quantity": 5})
    resp = client.delete(f"/api/lots/{lot['id']}")
    assert resp.status_code == 409


def test_void_dispatch_restores_quantity(client, lot):
    d = client.post("/api/dispatches", json={"lot_id": lot["id"], "partner": "Shelter", "quantity": 40}).json()
    assert client.delete(f"/api/dispatches/{d['id']}").status_code == 204
    restored = client.get(f"/api/lots/{lot['id']}").json()
    assert restored["quantity"] == 40
    assert restored["status"] == "available"
    assert client.get("/api/dispatches").json() == []
