"""Redis cache repository for transport segments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
import json
import logging
from typing import Protocol

from config import settings

from app.schemas.routes_api import TransportType
from app.services.providers.types import ProviderSegment, SegmentSearchQuery

logger = logging.getLogger("app.segment_cache_repository")


class AsyncCacheClientProtocol(Protocol):
    """Protocol for async cache clients used by the repository."""

    async def get(self, key: str):  # noqa: ANN201
        """Return cached value by key."""

    async def set(self, key: str, value: str, ex: int) -> bool:
        """Persist value by key with expiration in seconds."""

    async def delete(self, key: str) -> int:
        """Delete value by key and return affected count."""


@dataclass(slots=True)
class CacheMetrics:
    """Cache counters for observability."""

    hits: int = 0
    misses: int = 0
    stale: int = 0
    errors: int = 0


class SegmentCacheRepository:
    """Cache-aside repository for provider segments with Redis backend."""

    def __init__(
        self,
        client: AsyncCacheClientProtocol | None = None,
        ttl_seconds: int | None = None,
    ) -> None:
        """Initialize repository with optional injected cache client."""
        self._client = client
        self._ttl_seconds = ttl_seconds or settings.redis_segments_ttl_seconds
        self._metrics = CacheMetrics()

        if self._client is None:
            self._client = self._build_default_client()

    @property
    def metrics(self) -> CacheMetrics:
        """Expose cache metrics counters."""
        return self._metrics

    @staticmethod
    def build_key(query: SegmentSearchQuery) -> str:
        """Build cache key for segment search query."""
        return f"segment:{query.origin_id}:{query.destination_id}:{query.date.isoformat()}"

    async def get_segments(self, query: SegmentSearchQuery) -> list[ProviderSegment] | None:
        """Read and deserialize segments from cache if available."""
        if self._client is None:
            self._metrics.errors += 1
            return None

        key = self.build_key(query)
        try:
            value = await self._client.get(key)
            if not value:
                self._metrics.misses += 1
                return None

            parsed = json.loads(value)
            expires_at = datetime.fromisoformat(parsed["expires_at"])
            now = datetime.now(UTC)
            if expires_at <= now:
                self._metrics.stale += 1
                return None

            segments = [self._deserialize_segment(item) for item in parsed["segments"]]
            self._metrics.hits += 1
            return segments
        except Exception as exc:  # noqa: BLE001
            self._metrics.errors += 1
            logger.exception("Segment cache read failed", extra={"key": key, "error": str(exc)})
            return None

    async def set_segments(
        self,
        query: SegmentSearchQuery,
        segments: list[ProviderSegment],
    ) -> None:
        """Serialize and store segments in cache with configured TTL."""
        if self._client is None:
            self._metrics.errors += 1
            return

        key = self.build_key(query)
        payload = {
            "expires_at": (
                datetime.now(UTC).replace(microsecond=0)
                + timedelta(seconds=self._ttl_seconds)
            ).isoformat(),
            "segments": [self._serialize_segment(item) for item in segments],
        }
        try:
            await self._client.set(key, json.dumps(payload), ex=self._ttl_seconds)
        except Exception as exc:  # noqa: BLE001
            self._metrics.errors += 1
            logger.exception("Segment cache write failed", extra={"key": key, "error": str(exc)})

    async def invalidate(self, query: SegmentSearchQuery) -> None:
        """Invalidate cache entry by query key."""
        if self._client is None:
            self._metrics.errors += 1
            return
        key = self.build_key(query)
        try:
            await self._client.delete(key)
        except Exception as exc:  # noqa: BLE001
            self._metrics.errors += 1
            logger.exception("Segment cache invalidate failed", extra={"key": key, "error": str(exc)})

    @staticmethod
    def _serialize_segment(segment: ProviderSegment) -> dict:
        """Convert provider segment to JSON-serializable dict."""
        return {
            "provider": segment.provider,
            "transport_type": segment.transport_type.value,
            "external_id": segment.external_id,
            "origin_hub_id": segment.origin_hub_id,
            "destination_hub_id": segment.destination_hub_id,
            "departure_time": segment.departure_time.isoformat(),
            "arrival_time": segment.arrival_time.isoformat(),
            "duration_minutes": segment.duration_minutes,
            "price_amount": str(segment.price_amount),
            "currency": segment.currency,
            "raw_payload": segment.raw_payload,
        }

    @staticmethod
    def _deserialize_segment(payload: dict) -> ProviderSegment:
        """Convert cached dict back to provider segment."""
        return ProviderSegment(
            provider=str(payload["provider"]),
            transport_type=TransportType(payload["transport_type"]),
            external_id=str(payload["external_id"]),
            origin_hub_id=int(payload["origin_hub_id"]),
            destination_hub_id=int(payload["destination_hub_id"]),
            departure_time=datetime.fromisoformat(payload["departure_time"]),
            arrival_time=datetime.fromisoformat(payload["arrival_time"]),
            duration_minutes=int(payload["duration_minutes"]),
            price_amount=Decimal(str(payload["price_amount"])),
            currency=str(payload["currency"]),
            raw_payload=payload.get("raw_payload"),
        )

    @staticmethod
    def _build_default_client() -> AsyncCacheClientProtocol | None:
        """Create redis async client from config or return None when unavailable."""
        try:
            from redis.asyncio import Redis
        except Exception:  # noqa: BLE001
            logger.warning("redis.asyncio is unavailable; cache disabled")
            return None
        try:
            return Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis client initialization failed", extra={"error": str(exc)})
            return None
