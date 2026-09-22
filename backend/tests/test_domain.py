from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db import SessionLocal
from app.main import app
from app.models import Issue, Property, Reservation, User

client = TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    created_property_ids: list[int] = []
    try:
        if session.get(User, 1) is None:
            session.add(User(id=1, name="Alex Guest", email="alex@example.com"))
            session.commit()
        yield session, created_property_ids
    finally:
        if created_property_ids:
            reservation_ids = list(
                session.scalars(
                    select(Reservation.id).where(
                        Reservation.property_id.in_(created_property_ids)
                    )
                )
            )
            if reservation_ids:
                session.execute(delete(Issue).where(Issue.reservation_id.in_(reservation_ids)))
                session.execute(delete(Reservation).where(Reservation.id.in_(reservation_ids)))
            session.execute(delete(Property).where(Property.id.in_(created_property_ids)))
            session.commit()
        session.close()


def _property(db_session, **overrides) -> Property:
    data = {
        "title": "Test Loft",
        "description": "A test stay.",
        "city": "Testville",
        "price_per_night": 100,
        "max_guests": 2,
        "amenities": ["wifi"],
        "house_rules": "No parties.",
        "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
        "lat": 0.0,
        "lng": 0.0,
        "nearby": [{"name": "Test Cafe", "kind": "restaurant", "blurb": "Nearby."}],
    }
    data.update(overrides)
    prop = Property(**data)
    db_session.add(prop)
    db_session.commit()
    db_session.refresh(prop)
    return prop


def test_list_and_filter_properties(db):
    session, created = db
    cheap = _property(session, title="Cheap Loft", city="Filtertown", price_per_night=90, max_guests=2)
    expensive = _property(
        session, title="Pricey Loft", city="Filtertown", price_per_night=400, max_guests=6
    )
    created.extend([cheap.id, expensive.id])

    response = client.get("/properties", params={"city": "filtertown", "max_price": 150, "guests": 2})
    assert response.status_code == 200
    titles = [row["title"] for row in response.json()]
    assert titles == ["Cheap Loft"]

    detail = client.get(f"/properties/{cheap.id}")
    assert detail.status_code == 200
    assert detail.json()["house_rules"] == "No parties."
    assert detail.json()["nearby"][0]["name"] == "Test Cafe"


def test_book_extend_cancel_and_issue(db):
    session, created = db
    prop = _property(session, max_guests=2)
    created.append(prop.id)
    check_in = date.today() + timedelta(days=40)
    check_out = check_in + timedelta(days=3)

    booked = client.post(
        "/reservations",
        json={
            "property_id": prop.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "guests": 2,
        },
    )
    assert booked.status_code == 201
    reservation_id = booked.json()["id"]
    assert booked.json()["status"] == "confirmed"

    overlap = client.post(
        "/reservations",
        json={
            "property_id": prop.id,
            "check_in": (check_in + timedelta(days=1)).isoformat(),
            "check_out": (check_out + timedelta(days=1)).isoformat(),
            "guests": 1,
        },
    )
    assert overlap.status_code == 409

    extended = client.patch(
        f"/reservations/{reservation_id}",
        json={"action": "extend", "check_out": (check_out + timedelta(days=2)).isoformat()},
    )
    assert extended.status_code == 200
    assert extended.json()["check_out"] == (check_out + timedelta(days=2)).isoformat()

    issue = client.post(
        f"/reservations/{reservation_id}/issues",
        json={"description": "The sink is dripping."},
    )
    assert issue.status_code == 201
    assert issue.json()["status"] == "open"

    cancelled = client.patch(f"/reservations/{reservation_id}", json={"action": "cancel"})
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"

    second_issue = client.post(
        f"/reservations/{reservation_id}/issues",
        json={"description": "Too late."},
    )
    assert second_issue.status_code == 409

    listed = client.get("/reservations")
    assert listed.status_code == 200
    assert any(row["id"] == reservation_id for row in listed.json())


def test_missing_property_and_bad_dates(db):
    session, created = db
    prop = _property(session)
    created.append(prop.id)
    missing = client.get("/properties/999999")
    assert missing.status_code == 404

    bad = client.post(
        "/reservations",
        json={
            "property_id": prop.id,
            "check_in": "2026-10-10",
            "check_out": "2026-10-10",
            "guests": 1,
        },
    )
    assert bad.status_code == 422
    too_many = client.post(
        "/reservations",
        json={
            "property_id": prop.id,
            "check_in": "2026-11-01",
            "check_out": "2026-11-04",
            "guests": 9,
        },
    )
    assert too_many.status_code == 422
