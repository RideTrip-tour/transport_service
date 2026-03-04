from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from app.crud.route_crud import RouteCrud
from app.schemas.routes_api import (
    RouteBatchRecalculateRequest,
    RoutePreferences,
    RouteSearchRequest,
    TransportType,
)
from app.services.cache.segment_cache_repository import SegmentCacheRepository
from app.services.providers.base import ProviderAdapter
from app.services.providers.registry import ProviderRegistry
from app.services.providers.types import ProviderSegment, SegmentSearchQuery
from app.services.route_application import DbRouteApplicationService


class _FakeCacheClient:
    def __init__(self) -> None:
        self.storage: dict[str, str] = {}

    async def get(self, key: str):
        return self.storage.get(key)

    async def set(self, key: str, value: str, ex: int) -> bool:  # noqa: ARG002
        self.storage[key] = value
        return True

    async def delete(self, key: str) -> int:
        return 1 if self.storage.pop(key, None) is not None else 0


class _CountingFlightAdapter(ProviderAdapter):
    def __init__(self) -> None:
        super().__init__(max_concurrency=1)
        self.calls = 0

    @property
    def transport_type(self) -> TransportType:
        return TransportType.FLIGHT

    @property
    def provider_name(self) -> str:
        return "counting_flight"

    async def fetch_segments(self, query: SegmentSearchQuery) -> list[ProviderSegment]:
        self.calls += 1
        now = datetime.now(UTC)
        return [
            ProviderSegment(
                provider=self.provider_name,
                transport_type=TransportType.FLIGHT,
                external_id=f"seg-{query.origin_id}-{query.destination_id}-{idx}",
                origin_hub_id=query.origin_id,
                destination_hub_id=query.destination_id,
                departure_time=now + timedelta(hours=idx + 1),
                arrival_time=now + timedelta(hours=idx + 2),
                duration_minutes=60,
                price_amount=Decimal("40.00") + Decimal(idx),
                currency="USD",
                raw_payload={"source": "provider"},
            )
            for idx in range(query.top_n)
        ]


@pytest.mark.asyncio
async def test_search_uses_cache_aside_and_skips_second_provider_call(db_session_factory):
    adapter = _CountingFlightAdapter()
    cache = SegmentCacheRepository(client=_FakeCacheClient(), ttl_seconds=3600)
    service = DbRouteApplicationService(
        provider_registry=ProviderRegistry([adapter]),
        segment_cache_repository=cache,
    )
    payload = RouteSearchRequest(
        origin_id=10,
        destination_id=20,
        date=date(2026, 4, 1),
        top_n=2,
        preferences=RoutePreferences(transport_types=[TransportType.FLIGHT]),
    )

    async with db_session_factory() as session:
        first = await service.search(session=session, payload=payload, user_id=1)
        second = await service.search(session=session, payload=payload, user_id=1)

    assert len(first.routes) == 2
    assert len(second.routes) == 2
    assert adapter.calls == 1
    assert cache.metrics.hits >= 1


@pytest.mark.asyncio
async def test_batch_recalculate_warms_cache_by_route_group(db_session_factory):
    adapter = _CountingFlightAdapter()
    cache = SegmentCacheRepository(client=_FakeCacheClient(), ttl_seconds=3600)
    service = DbRouteApplicationService(
        provider_registry=ProviderRegistry([adapter]),
        segment_cache_repository=cache,
    )

    async with db_session_factory() as session:
        route1 = await RouteCrud.create(
            session=session,
            data={
                "origin_location_id": 10,
                "destination_location_id": 20,
                "date": date(2026, 4, 1),
                "total_price": Decimal("10.00"),
                "currency": "USD",
                "total_duration_minutes": 60,
                "total_transfer_duration_minutes": 0,
                "transfers_count": 0,
                "score": Decimal("10.0000"),
                "segments_snapshot": [],
            },
        )
        route2 = await RouteCrud.create(
            session=session,
            data={
                "origin_location_id": 10,
                "destination_location_id": 20,
                "date": date(2026, 4, 1),
                "total_price": Decimal("11.00"),
                "currency": "USD",
                "total_duration_minutes": 70,
                "total_transfer_duration_minutes": 0,
                "transfers_count": 0,
                "score": Decimal("11.0000"),
                "segments_snapshot": [],
            },
        )
        await service.batch_recalculate(
            session=session,
            payload=RouteBatchRecalculateRequest(
                route_ids=[route1.id, route2.id],
                force_refresh=True,
            ),
        )

    assert adapter.calls == 1
