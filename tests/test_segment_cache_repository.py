import json
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from app.schemas.routes_api import TransportType
from app.services.cache import SegmentCacheRepository
from app.services.providers.types import ProviderSegment, SegmentSearchQuery


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


def _segment() -> ProviderSegment:
    now = datetime.now(UTC)
    return ProviderSegment(
        provider="flight_provider",
        transport_type=TransportType.FLIGHT,
        external_id="ext-1",
        origin_hub_id=10,
        destination_hub_id=20,
        departure_time=now + timedelta(hours=1),
        arrival_time=now + timedelta(hours=2),
        duration_minutes=60,
        price_amount=Decimal("55.50"),
        currency="USD",
        raw_payload={"from": "test"},
    )


@pytest.mark.asyncio
async def test_segment_cache_repository_set_and_get_hit_metrics():
    client = _FakeCacheClient()
    repo = SegmentCacheRepository(client=client, ttl_seconds=3600)
    query = SegmentSearchQuery(origin_id=10, destination_id=20, date=date(2026, 4, 1), top_n=2)

    await repo.set_segments(query, [_segment()])
    cached = await repo.get_segments(query)

    assert cached is not None
    assert len(cached) == 1
    assert cached[0].external_id == "ext-1"
    assert repo.metrics.hits == 1
    assert repo.metrics.misses == 0


@pytest.mark.asyncio
async def test_segment_cache_repository_miss_and_stale_metrics():
    client = _FakeCacheClient()
    repo = SegmentCacheRepository(client=client, ttl_seconds=3600)
    query = SegmentSearchQuery(origin_id=10, destination_id=20, date=date(2026, 4, 1), top_n=2)

    miss = await repo.get_segments(query)
    assert miss is None
    assert repo.metrics.misses == 1

    key = repo.build_key(query)
    stale_payload = {
        "expires_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
        "segments": [repo._serialize_segment(_segment())],  # noqa: SLF001
    }
    client.storage[key] = json.dumps(stale_payload)
    stale = await repo.get_segments(query)
    assert stale is None
    assert repo.metrics.stale == 1

