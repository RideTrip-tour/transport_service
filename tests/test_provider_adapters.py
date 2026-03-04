from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from config import settings
from app.schemas.routes_api import TransportType
from app.services.providers import (
    FlightProviderAdapter,
    ProviderRegistry,
    SegmentSearchQuery,
)
from app.services.providers.base import ProviderAdapter
from app.services.providers.types import ProviderSegment


@pytest.mark.asyncio
async def test_flight_adapter_maps_payload_to_provider_segment(monkeypatch):
    adapter = FlightProviderAdapter()

    async def fake_request(_query):
        return [
            {
                "provider": "flight_x",
                "external_id": "ext-1",
                "origin_hub_id": 10,
                "destination_hub_id": 20,
                "departure_time": "2026-04-01T10:00:00Z",
                "arrival_time": "2026-04-01T12:00:00Z",
                "price_amount": "55.50",
                "currency": "usd",
            }
        ]

    monkeypatch.setattr(adapter, "_request_segments", fake_request)

    segments = await adapter.fetch_segments(
        SegmentSearchQuery(origin_id=10, destination_id=20, date=date(2026, 4, 1), top_n=1)
    )
    assert len(segments) == 1
    assert segments[0].provider == "flight_x"
    assert segments[0].transport_type == TransportType.FLIGHT
    assert segments[0].price_amount == Decimal("55.50")
    assert segments[0].currency == "USD"


@pytest.mark.asyncio
async def test_flight_adapter_fallback_when_empty_payload(monkeypatch):
    adapter = FlightProviderAdapter()

    async def fake_request(_query):
        return []

    monkeypatch.setattr(adapter, "_request_segments", fake_request)
    segments = await adapter.fetch_segments(
        SegmentSearchQuery(origin_id=10, destination_id=20, date=date(2026, 4, 1), top_n=2)
    )
    assert len(segments) == 2
    assert all(item.raw_payload and item.raw_payload.get("fallback") for item in segments)


@pytest.mark.asyncio
async def test_flight_adapter_request_retries_then_success(monkeypatch):
    adapter = FlightProviderAdapter()
    monkeypatch.setattr(settings, "schedule_provider_retries", 1)
    monkeypatch.setattr(settings, "schedule_provider_base_url", "http://schedule-provider.test")
    calls = {"count": 0}

    class _Resp:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    class _Client:
        def __init__(self, *args, **kwargs):  # noqa: ARG002
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):  # noqa: ARG002
            return None

        async def get(self, url, params=None):  # noqa: ARG002
            calls["count"] += 1
            if calls["count"] == 1:
                raise RuntimeError("temporary failure")
            return _Resp(
                200,
                [
                    {
                        "provider": "flight_x",
                        "external_id": "ret-1",
                        "origin_hub_id": params["origin_id"],
                        "destination_hub_id": params["destination_id"],
                        "departure_time": "2026-04-01T10:00:00Z",
                        "arrival_time": "2026-04-01T12:00:00Z",
                        "price_amount": "33.10",
                        "currency": "USD",
                    }
                ],
            )

    monkeypatch.setattr("app.services.providers.flight_adapter.httpx.AsyncClient", _Client)
    segments = await adapter.fetch_segments(
        SegmentSearchQuery(origin_id=10, destination_id=20, date=date(2026, 4, 1), top_n=1)
    )
    assert calls["count"] == 2
    assert len(segments) == 1
    assert segments[0].external_id == "ret-1"


class _FakeAdapter(ProviderAdapter):
    def __init__(self, transport_type: TransportType, price: str):
        super().__init__(max_concurrency=1)
        self._transport_type = transport_type
        self._price = Decimal(price)

    @property
    def transport_type(self) -> TransportType:
        return self._transport_type

    @property
    def provider_name(self) -> str:
        return f"{self._transport_type.value}_provider"

    async def fetch_segments(self, query: SegmentSearchQuery) -> list[ProviderSegment]:
        return [
            ProviderSegment(
                provider=self.provider_name,
                transport_type=self._transport_type,
                external_id=f"{self._transport_type.value}-1",
                origin_hub_id=query.origin_id,
                destination_hub_id=query.destination_id,
                departure_time=datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2026, 4, 1, 11, 30, tzinfo=timezone.utc),
                duration_minutes=90,
                price_amount=self._price,
                currency="USD",
                raw_payload={"source": self.provider_name},
            )
        ]


@pytest.mark.asyncio
async def test_provider_registry_filters_by_transport_types():
    registry = ProviderRegistry(
        adapters=[
            _FakeAdapter(TransportType.FLIGHT, "40.00"),
            _FakeAdapter(TransportType.BUS, "20.00"),
        ]
    )
    query = SegmentSearchQuery(origin_id=1, destination_id=2, date=date(2026, 4, 1), top_n=5)

    flight_only = await registry.fetch_segments(query, [TransportType.FLIGHT])
    assert len(flight_only) == 1
    assert flight_only[0].transport_type == TransportType.FLIGHT

    both = await registry.fetch_segments(query, [TransportType.FLIGHT, TransportType.BUS])
    assert len(both) == 2
