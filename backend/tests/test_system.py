def test_health_is_up(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "UP"}


def test_ready_checks_database(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "READY"


def test_ready_reports_unmigrated_schema(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "require_migrations", True)
    resp = client.get("/ready")
    assert resp.status_code == 503
    assert resp.json()["status"] == "NOT_READY"


def test_metrics_exposes_prometheus_format(client):
    client.get("/api/lots")
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    assert "http_requests_total" in resp.text
    assert "http_request_duration_seconds" in resp.text


def test_info_reports_git_sha(client):
    body = client.get("/api/info").json()
    assert body["service"] == "PantryPulse API"
    assert "git_sha" in body
