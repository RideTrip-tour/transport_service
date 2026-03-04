import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from starlette.requests import Request
from sqlalchemy import select

from app.db.models import Route, SearchHistory
from app.routes import routes
from app.services.route_application import DbRouteApplicationService
from main import app


@pytest.fixture(autouse=True)
def reset_service(override_db_dependency):
    _ = override_db_dependency
    routes.route_service = DbRouteApplicationService()
    async def _always_exists(_location_id):
        return True
    routes.location_client.ensure_location_exists = _always_exists


@pytest.mark.asyncio
async def test_search_routes_returns_top_n_items(db_session_factory):
    client = TestClient(app)
    response = client.post(
        "/api/transport/routes/search",
        json={
            "origin_id": 10,
            "destination_id": 20,
            "date": "2026-04-01",
            "top_n": 3,
            "sort_by": "balanced",
            "preferences": {},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["routes"]) == 3
    assert body["routes"][0]["origin_id"] == 10
    assert body["routes"][0]["destination_id"] == 20
    assert body["routes"][0]["route_version"] == 1
    assert "score_breakdown" in body["routes"][0]
    async with db_session_factory() as session:
        route_rows = list((await session.execute(select(Route))).scalars().all())
        history_rows = list((await session.execute(select(SearchHistory))).scalars().all())
        routes_count = len(route_rows)
        history_count = len(history_rows)
    assert routes_count == 3
    assert history_count == 3
    assert history_rows[0].user_id is None


def test_extract_user_id_from_request_state_user_data():
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/transport/routes/search",
            "headers": [],
        }
    )
    request.state.user_data = {"user_id": 123, "is_active": True}
    assert routes._extract_user_id(request) == 123


def test_extract_user_id_supports_id_and_sub_keys():
    request_with_id = Request(
        {"type": "http", "method": "POST", "path": "/", "headers": []}
    )
    request_with_id.state.user_data = {"id": "77"}
    assert routes._extract_user_id(request_with_id) == 77

    request_with_sub = Request(
        {"type": "http", "method": "POST", "path": "/", "headers": []}
    )
    request_with_sub.state.user_data = {"sub": "88"}
    assert routes._extract_user_id(request_with_sub) == 88


@pytest.mark.asyncio
async def test_search_routes_persists_extracted_user_id(monkeypatch, db_session_factory):
    monkeypatch.setattr(routes, "_extract_user_id", lambda _request: 321)
    client = TestClient(app)
    response = client.post(
        "/api/transport/routes/search",
        json={
            "origin_id": 10,
            "destination_id": 20,
            "date": "2026-04-01",
            "top_n": 1,
            "sort_by": "balanced",
            "preferences": {},
        },
    )
    assert response.status_code == 200

    async with db_session_factory() as session:
        history_rows = list((await session.execute(select(SearchHistory))).scalars().all())
    assert len(history_rows) == 1
    assert history_rows[0].user_id == 321


def test_search_routes_validates_origin_and_destination():
    client = TestClient(app)
    response = client.post(
        "/api/transport/routes/search",
        json={
            "origin_id": 10,
            "destination_id": 10,
            "date": "2026-04-01",
            "top_n": 1,
            "sort_by": "time",
            "preferences": {},
        },
    )

    assert response.status_code == 422


def test_search_routes_returns_422_for_unknown_location(monkeypatch):
    async def _missing(location_id):  # noqa: ARG001
        return False

    monkeypatch.setattr(routes.location_client, "ensure_location_exists", _missing)
    client = TestClient(app)
    response = client.post(
        "/api/transport/routes/search",
        json={
            "origin_id": 10,
            "destination_id": 20,
            "date": "2026-04-01",
            "top_n": 1,
            "sort_by": "time",
            "preferences": {},
        },
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"


def test_search_routes_returns_503_when_location_service_unavailable(monkeypatch):
    async def _raise(location_id):  # noqa: ARG001
        raise routes.LocationServiceUnavailableError("boom")

    monkeypatch.setattr(routes.location_client, "ensure_location_exists", _raise)
    client = TestClient(app)
    response = client.post(
        "/api/transport/routes/search",
        json={
            "origin_id": 10,
            "destination_id": 20,
            "date": "2026-04-01",
            "top_n": 1,
            "sort_by": "time",
            "preferences": {},
        },
    )
    assert response.status_code == 503
    body = response.json()
    assert body["code"] == "DEPENDENCY_UNAVAILABLE"


def test_recalculate_route_increments_version():
    client = TestClient(app)
    search = client.post(
        "/api/transport/routes/search",
        json={
            "origin_id": 10,
            "destination_id": 20,
            "date": "2026-04-01",
            "top_n": 1,
            "sort_by": "balanced",
            "preferences": {},
        },
    )
    route_id = search.json()["routes"][0]["route_id"]

    response = client.post(
        f"/api/transport/routes/{route_id}/recalculate",
        json={"force_refresh": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["changed"] is True
    assert body["route"]["route_version"] == 2
    assert body["recalculated_at"]


def test_recalculate_is_idempotent_for_same_key():
    client = TestClient(app)
    search = client.post(
        "/api/transport/routes/search",
        json={
            "origin_id": 10,
            "destination_id": 20,
            "date": "2026-04-01",
            "top_n": 1,
            "sort_by": "balanced",
            "preferences": {},
        },
    )
    route_id = search.json()["routes"][0]["route_id"]
    first = client.post(
        f"/api/transport/routes/{route_id}/recalculate",
        json={"force_refresh": True},
        headers={"Idempotency-Key": "same-key-1"},
    )
    second = client.post(
        f"/api/transport/routes/{route_id}/recalculate",
        json={"force_refresh": True},
        headers={"Idempotency-Key": "same-key-1"},
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["route"]["route_version"] == 2
    assert second.json()["route"]["route_version"] == 2


def test_recalculate_unknown_route_returns_unified_error():
    client = TestClient(app)
    response = client.post(
        "/api/transport/routes/999999/recalculate",
        json={"force_refresh": True},
    )

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "NOT_FOUND"
    assert body["message"] == "Route not found"
    assert body["details"]["route_id"] == 999999
    assert body["trace_id"]


def test_batch_recalculate_returns_partial_statuses():
    client = TestClient(app)
    search = client.post(
        "/api/transport/routes/search",
        json={
            "origin_id": 10,
            "destination_id": 20,
            "date": "2026-04-01",
            "top_n": 2,
            "sort_by": "price",
            "preferences": {},
        },
    )
    first = search.json()["routes"][0]["route_id"]
    second = search.json()["routes"][1]["route_id"]

    response = client.post(
        "/api/transport/routes/batch-recalculate",
        json={"route_ids": [first, second, 999999], "force_refresh": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["batch_id"] is not None
    assert body["updated"] == 2
    assert body["failed"] == 1
    statuses = {item["route_id"]: item["status"] for item in body["items"]}
    assert statuses[first] == "updated"
    assert statuses[second] == "updated"
    assert statuses[999999] == "not_found"


def test_batch_recalculate_trigger_endpoint_returns_202():
    client = TestClient(app)
    search = client.post(
        "/api/transport/routes/search",
        json={
            "origin_id": 10,
            "destination_id": 20,
            "date": "2026-04-01",
            "top_n": 1,
            "sort_by": "price",
            "preferences": {},
        },
    )
    route_id = search.json()["routes"][0]["route_id"]

    response = client.post(
        "/api/transport/routes/batch-recalculate/trigger",
        json={"route_ids": [route_id], "force_refresh": True, "max_concurrency": 2},
    )
    assert response.status_code == 202
    body = response.json()
    assert body["batch_id"] is not None
    assert body["updated"] == 1


def test_old_planner_endpoint_is_not_available():
    client = TestClient(app)
    response = client.post(
        "/api/transport/planner/compose",
        json={
            "from_location_id": 10,
            "to_location_id": 20,
            "optimization": "fastest",
        },
    )

    assert response.status_code == 404
