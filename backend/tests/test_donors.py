def test_create_and_list_donors(client, donor):
    resp = client.get("/api/donors")
    assert resp.status_code == 200
    assert [d["name"] for d in resp.json()] == ["Kalinga Organic Farms"]


def test_duplicate_donor_name_returns_409(client, donor):
    resp = client.post("/api/donors", json={"name": "Kalinga Organic Farms", "kind": "farm", "city": "Puri"})
    assert resp.status_code == 409


def test_donor_validation(client):
    resp = client.post(
        "/api/donors", json={"name": " ", "kind": "spaceship", "city": "X", "contact_email": "not-an-email"}
    )
    assert resp.status_code == 422
    fields = {err["loc"][-1] for err in resp.json()["detail"]}
    assert {"name", "kind", "city", "contact_email"} <= fields


def test_update_donor(client, donor):
    resp = client.put(f"/api/donors/{donor['id']}", json={"city": "Bhubaneswar"})
    assert resp.status_code == 200
    assert resp.json()["city"] == "Bhubaneswar"


def test_get_missing_donor_returns_404(client):
    assert client.get("/api/donors/404").status_code == 404


def test_delete_donor_keeps_lots(client, lot):
    donor_id = lot["donor_id"]
    assert client.get(f"/api/donors/{donor_id}").json()["lot_count"] == 1
    assert client.delete(f"/api/donors/{donor_id}").status_code == 204
    orphan = client.get(f"/api/lots/{lot['id']}").json()
    assert orphan["donor_id"] is None
    assert orphan["donor_name"] is None
