from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert "status" in payload
    assert payload["database"] in {"up", "down"}


def test_responses_carry_served_by_header() -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.headers["X-Api-Pod"] == response.json()["pod"]


def test_liveness_ignores_database_outage() -> None:
    with patch("app.main._database_up", return_value=False):
        assert client.get("/health/live").status_code == 200


def test_readiness_fails_when_database_down() -> None:
    with patch("app.main._database_up", return_value=False):
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["database"] == "down"
