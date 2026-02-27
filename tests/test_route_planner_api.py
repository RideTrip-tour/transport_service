from decimal import Decimal

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from app.db.database import get_async_session
from app.routes import route_planner
from app.schemas.planner import ComposeRouteResponse, RouteSegment
from main import app


async def _dummy_session():
    yield None


def test_compose_route_success(monkeypatch):
    async def always_exists(_):
        return True

    async def fake_compose(*args, **kwargs):  # noqa: ARG001
        return ComposeRouteResponse(
            total_duration_minutes=90,
            total_price_amount=Decimal("59.50"),
            currency="USD",
            transfers=1,
            segments=[
                RouteSegment(
                    route_id=1,
                    transport_type_id=2,
                    from_location_id=10,
                    to_location_id=20,
                    duration_minutes=90,
                    price_amount=Decimal("59.50"),
                    currency="USD",
                )
            ],
        )

    monkeypatch.setattr(
        route_planner.location_client, "ensure_location_exists", always_exists
    )
    monkeypatch.setattr(route_planner.planner_service, "compose", fake_compose)
    app.dependency_overrides[get_async_session] = _dummy_session

    try:
        client = TestClient(app)
        response = client.post(
            "/api/transport/planner/compose",
            json={
                "from_location_id": 10,
                "to_location_id": 20,
                "optimization": "fastest",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["transfers"] == 1


def test_compose_route_returns_422_for_unknown_location(monkeypatch):
    async def missing_location(_):
        return False

    monkeypatch.setattr(
        route_planner.location_client, "ensure_location_exists", missing_location
    )
    app.dependency_overrides[get_async_session] = _dummy_session

    try:
        client = TestClient(app)
        response = client.post(
            "/api/transport/planner/compose",
            json={
                "from_location_id": 10,
                "to_location_id": 20,
                "optimization": "fastest",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
