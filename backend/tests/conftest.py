"""Test fixtures.

The API never touches the development or production database during tests:
each test gets a fresh in-memory SQLite database wired in through FastAPI's
dependency override. PostgreSQL-specific checks live in test_postgres.py and
only run when TEST_POSTGRES_URL points at a throwaway database (CI service).
"""

import os
from collections.abc import Iterator
from datetime import date, timedelta

# Must be set before the app (and its module-level engine) is imported.
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["REQUIRE_MIGRATIONS"] = "false"
os.environ["LOG_LEVEL"] = "WARNING"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _):  # SQLite ignores foreign keys unless asked
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = testing_session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Iterator[TestClient]:
    def _override() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def donor(client: TestClient) -> dict:
    resp = client.post(
        "/api/donors",
        json={"name": "Kalinga Organic Farms", "kind": "farm", "city": "Cuttack", "contact_email": "farm@example.org"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def lot_payload(**overrides) -> dict:
    today = date.today()
    payload = {
        "item_name": "Tomatoes",
        "category": "produce",
        "quantity": 40,
        "unit": "kg",
        "storage": "chilled",
        "received_on": today.isoformat(),
        "expires_on": (today + timedelta(days=5)).isoformat(),
    }
    payload.update(overrides)
    return payload


@pytest.fixture()
def lot(client: TestClient, donor: dict) -> dict:
    resp = client.post("/api/lots", json=lot_payload(donor_id=donor["id"]))
    assert resp.status_code == 201, resp.text
    return resp.json()
