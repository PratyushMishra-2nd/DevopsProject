"""Runs Alembic migrations and the API against a real PostgreSQL.

Skipped unless TEST_POSTGRES_URL is set (the CI job starts a throwaway
postgres service container for this). Never point it at a real database:
the fixture downgrades the schema to base at the end.
"""

import os
from collections.abc import Iterator

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from alembic import command
from app.config import get_settings
from app.db import get_db
from app.main import app
from tests.conftest import lot_payload

PG_URL = os.environ.get("TEST_POSTGRES_URL")
pytestmark = [pytest.mark.postgres, pytest.mark.skipif(not PG_URL, reason="TEST_POSTGRES_URL not set")]


@pytest.fixture()
def pg_client(monkeypatch) -> Iterator[TestClient]:
    settings = get_settings()
    monkeypatch.setattr(settings, "database_url", PG_URL)
    monkeypatch.setattr(settings, "require_migrations", True)
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    engine = create_engine(PG_URL)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)

    def _override() -> Iterator[Session]:
        with testing_session() as s:
            yield s

    app.dependency_overrides[get_db] = _override
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
        command.downgrade(cfg, "base")


def test_migrations_create_expected_tables(pg_client):
    engine = create_engine(PG_URL)
    assert {"donors", "stock_lots", "dispatches", "alembic_version"} <= set(inspect(engine).get_table_names())
    with engine.connect() as conn:
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0002_dispatches"
    engine.dispose()


def test_ready_and_crud_on_postgres(pg_client):
    assert pg_client.get("/ready").json() == {"status": "READY"}
    created = pg_client.post("/api/lots", json=lot_payload()).json()
    d = pg_client.post("/api/dispatches", json={"lot_id": created["id"], "partner": "Shelter", "quantity": 10})
    assert d.status_code == 201
    assert pg_client.get(f"/api/lots/{created['id']}").json()["quantity"] == 30
    assert pg_client.delete(f"/api/lots/{created['id']}").status_code == 409
