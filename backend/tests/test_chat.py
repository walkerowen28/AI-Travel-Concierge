from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.agent.context import ConciergeContext
from app.agent import tools as tool_module
from app.db import SessionLocal
from app.main import app
from app.models import Property, Reservation, ReservationStatus, User

client = TestClient(app)


def _ensure_user(session) -> None:
    if session.get(User, 1) is None:
        session.add(User(id=1, name="Alex Guest", email="alex-chat@example.com"))
        session.commit()


def _property(session, **overrides) -> Property:
    data = {
        "title": "Chat Test Loft",
        "description": "A test stay for the concierge.",
        "city": "Chatville",
        "price_per_night": 120,
        "max_guests": 2,
        "amenities": ["wifi"],
        "house_rules": "Quiet after 10pm.",
        "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
        "lat": 1.0,
        "lng": 2.0,
        "nearby": [{"name": "Test Cafe", "kind": "restaurant", "blurb": "Good lunch."}],
    }
    data.update(overrides)
    prop = Property(**data)
    session.add(prop)
    session.commit()
    session.refresh(prop)
    return prop


def _cleanup(session, property_ids: list[int]) -> None:
    if not property_ids:
        return
    from sqlalchemy import select

    from app.models import Issue

    reservation_ids = list(
        session.scalars(select(Reservation.id).where(Reservation.property_id.in_(property_ids)))
    )
    if reservation_ids:
        session.execute(delete(Issue).where(Issue.reservation_id.in_(reservation_ids)))
        session.execute(delete(Reservation).where(Reservation.id.in_(reservation_ids)))
    session.execute(delete(Property).where(Property.id.in_(property_ids)))
    session.commit()


def test_search_properties_tool_uses_service_layer():
    session = SessionLocal()
    created_ids: list[int] = []
    try:
        _ensure_user(session)
        prop = _property(session, city="Tooltown", price_per_night=99)
        created_ids.append(prop.id)
        context = ConciergeContext(db=session)
        wrapper = type("W", (), {"context": context})()

        result = tool_module.search_properties.__wrapped__(
            wrapper,
            city="Tooltown",
            max_price=150,
            guests=1,
            check_in=None,
            check_out=None,
        )
        assert "Chat Test Loft" in result
        assert context.tool_traces[0]["tool"] == "search_properties"
    finally:
        _cleanup(session, created_ids)
        session.close()


def test_extend_stay_tool_updates_reservation():
    session = SessionLocal()
    created_property_ids: list[int] = []
    try:
        _ensure_user(session)
        prop = _property(session)
        created_property_ids.append(prop.id)
        check_in = date.today() + timedelta(days=60)
        check_out = check_in + timedelta(days=3)
        reservation = Reservation(
            user_id=1,
            property_id=prop.id,
            check_in=check_in,
            check_out=check_out,
            guests=1,
            status=ReservationStatus.CONFIRMED,
        )
        session.add(reservation)
        session.commit()
        session.refresh(reservation)

        context = ConciergeContext(db=session, reservation_id=reservation.id)
        wrapper = type("W", (), {"context": context})()
        new_out = (check_out + timedelta(days=2)).isoformat()
        result = tool_module.extend_stay.__wrapped__(
            wrapper,
            new_check_out=new_out,
            reservation_id=None,
        )
        assert "Extended reservation" in result
        session.refresh(reservation)
        assert reservation.check_out.isoformat() == new_out
        assert context.tool_traces[0]["tool"] == "extend_stay"
    finally:
        _cleanup(session, created_property_ids)
        session.close()


def test_chat_endpoint_returns_message_and_traces_when_runner_mocked():
    async def fake_run(_db, *, messages, reservation_id=None):
        assert messages[0]["content"]
        return {
            "message": "I found a loft in Austin.",
            "tool_traces": [{"tool": "search_properties", "detail": "results=2"}],
        }

    with patch("app.routers.chat.run_concierge", new=AsyncMock(side_effect=fake_run)):
        response = client.post(
            "/chat",
            json={"messages": [{"role": "user", "content": "Find a loft in Austin"}]},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"].startswith("I found")
    assert payload["tool_traces"][0]["tool"] == "search_properties"


def test_chat_requires_api_key_when_missing():
    with patch("app.agent.runner.get_settings") as mocked:
        mocked.return_value.openai_api_key = ""
        mocked.return_value.openai_model = "gpt-4.1-mini"
        response = client.post(
            "/chat",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
    assert response.status_code == 422
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_chat_maps_openai_quota_errors():
    from app.agent.runner import _raise_openai_error
    from app.errors import ValidationError

    class FakeRateLimit(Exception):
        pass

    try:
        _raise_openai_error(
            FakeRateLimit(
                "Error code: 429 - {'error': {'code': 'credit_balance_exhausted'}}"
            )
        )
        assert False, "expected ValidationError"
    except ValidationError as exc:
        assert "credits" in str(exc).lower()
