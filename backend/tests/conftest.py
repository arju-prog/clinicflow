"""Shared pytest fixtures.

Tests never touch PostgreSQL: every test gets a brand-new in-memory SQLite database,
wired into the app by overriding the `get_db` dependency.
"""

import os

# Must be set before `app` is imported, so the module-level engine is never pointed at Postgres.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SEED_DEMO_DATA"] = "false"

from datetime import UTC, datetime, timedelta  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # one shared connection => the in-memory DB survives across requests
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def future_slot(days: int = 1, hour: int = 10, minute: int = 0) -> str:
    base = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    return (base + timedelta(days=days, hours=hour, minutes=minute)).isoformat()


@pytest.fixture()
def make_doctor(client):
    counter = {"n": 0}

    def _make(**overrides):
        counter["n"] += 1
        payload = {
            "full_name": f"Dr. Test {counter['n']}",
            "specialty": "General Medicine",
            "email": f"doctor{counter['n']}@clinic.test",
            "room": "101",
        } | overrides
        response = client.post("/api/doctors", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture()
def make_patient(client):
    def _make(**overrides):
        payload = {
            "full_name": "Jane Patient",
            "date_of_birth": "1990-05-17",
            "gender": "FEMALE",
            "phone": "+91 98765 43210",
        } | overrides
        response = client.post("/api/patients", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture()
def book(client):
    def _book(doctor_id: int, patient_id: int, **overrides):
        payload = {
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "scheduled_at": future_slot(),
            "reason": "General consultation",
        } | overrides
        return client.post("/api/appointments", json=payload)

    return _book
