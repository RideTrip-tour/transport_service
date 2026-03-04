import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from app.routes import routes
from app.schemas.routes_api import TransportType
from app.services.cache.segment_cache_repository import SegmentCacheRepository
from app.services.observability import observability_registry
from app.services.providers.base import ProviderAdapter
from app.services.providers.registry import ProviderRegistry
from app.services.providers.types import ProviderSegment, SegmentSearchQuery
from app.services.route_application import DbRouteApplicationService
from config import settings
from main import app


class _FastAdapter(ProviderAdapter):
    """Deterministic no-network adapter for observability integration tests."""

    @property
    def transport_type(self) -> TransportType:
        return TransportType.FLIGHT

    @property
    def provider_name(self) -> str:
        return "fast_adapter"

    async def fetch_segments(self, query: SegmentSearchQuery) -> list[ProviderSegment]:
        from datetime import UTC, datetime, timedelta
        from decimal import Decimal

        now = datetime.now(UTC)
        return [
            ProviderSegment(
                provider=self.provider_name,
                transport_type=TransportType.FLIGHT,
                external_id=f"fast-{query.origin_id}-{query.destination_id}-{idx}",
                origin_hub_id=query.origin_id,
                destination_hub_id=query.destination_id,
                departure_time=now + timedelta(hours=idx + 1),
                arrival_time=now + timedelta(hours=idx + 2),
                duration_minutes=60,
                price_amount=Decimal("50.00"),
                currency="USD",
                raw_payload={"source": "test"},
            )
            for idx in range(query.top_n)
        ]


class _FakeCacheClient:
    """In-memory async cache implementation for deterministic tests."""

    def __init__(self) -> None:
        self.storage: dict[str, str] = {}

    async def get(self, key: str):
        return self.storage.get(key)

    async def set(self, key: str, value: str, ex: int) -> bool:  # noqa: ARG002
        self.storage[key] = value
        return True

    async def delete(self, key: str) -> int:
        return 1 if self.storage.pop(key, None) is not None else 0


@pytest.fixture(autouse=True)
def reset_service_and_metrics(override_db_dependency):
    """Reset service singleton and in-memory metrics for each test."""
    _ = override_db_dependency
    routes.route_service = DbRouteApplicationService(
        provider_registry=ProviderRegistry([_FastAdapter()]),
        segment_cache_repository=SegmentCacheRepository(client=_FakeCacheClient(), ttl_seconds=3600),
    )
    observability_registry.__init__()

    async def _always_exists(_location_id):
        return True

    routes.location_client.ensure_location_exists = _always_exists


def test_search_sets_correlation_headers():
    """Search response should always include correlation identifiers."""
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
        headers={"X-Request-ID": "req-1", "X-Trace-ID": "trace-1"},
    )
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-1"
    assert response.headers["X-Trace-ID"] == "trace-1"


def test_payload_size_guardrail_returns_413(monkeypatch):
    """Middleware should reject oversized requests before endpoint execution."""
    monkeypatch.setattr(settings, "max_request_body_bytes", 20)
    client = TestClient(app)
    response = client.post(
        "/api/transport/routes/search",
        json={
            "origin_id": 10,
            "destination_id": 20,
            "date": "2026-04-01",
            "top_n": 1,
            "sort_by": "balanced",
            "preferences": {"transport_types": ["flight"], "min_transfer_minutes": 20},
        },
    )
    assert response.status_code == 413
    body = response.json()
    assert body["code"] == "PAYLOAD_TOO_LARGE"
    assert "max_request_body_bytes" in body["details"]


def test_batch_size_guardrail_respects_runtime_limit(monkeypatch):
    """Batch should fail with unified validation error when runtime limit is exceeded."""
    monkeypatch.setattr(settings, "batch_max_size", 1)
    client = TestClient(app)
    response = client.post(
        "/api/transport/routes/batch-recalculate",
        json={"route_ids": [1, 2], "force_refresh": True},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["details"]["batch_max_size"] == 1


def test_metrics_endpoint_contains_operation_and_cache_stats():
    """Metrics endpoint should expose operation, provider and cache counters."""
    client = TestClient(app)
    _ = client.post(
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
    metrics = client.get("/api/transport/health/metrics")
    assert metrics.status_code == 200
    body = metrics.json()
    assert "search" in body["operations"]
    assert "cache" in body
    assert "hit_ratio" in body["cache"]


def test_ready_endpoint_returns_dependency_checks():
    """Readiness endpoint should include per-dependency status payload."""
    client = TestClient(app)
    response = client.get("/api/transport/health/ready")
    assert response.status_code in (200, 503)
    body = response.json()
    assert "checks" in body
    assert "database" in body["checks"]
    assert "redis" in body["checks"]
