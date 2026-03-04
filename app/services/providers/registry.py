from __future__ import annotations

import logging

from app.schemas.routes_api import TransportType
from app.services.observability import observability_registry
from app.services.providers.base import ProviderAdapter
from app.services.providers.types import ProviderSegment, SegmentSearchQuery

logger = logging.getLogger("app.provider_registry")


class ProviderRegistry:
    """Registry for typed provider adapters and fan-out segment loading."""

    def __init__(self, adapters: list[ProviderAdapter]) -> None:
        """Store adapters by transport type for later dispatch."""
        self._adapters = {adapter.transport_type: adapter for adapter in adapters}

    def get(self, transport_type: TransportType) -> ProviderAdapter | None:
        """Return adapter by transport type if registered."""
        return self._adapters.get(transport_type)

    async def fetch_segments(
        self,
        query: SegmentSearchQuery,
        transport_types: list[TransportType] | None,
    ) -> list[ProviderSegment]:
        """Fetch segments across selected providers with per-provider SLA metrics."""
        selected_types = transport_types or [TransportType.FLIGHT]
        segments: list[ProviderSegment] = []
        for transport_type in selected_types:
            adapter = self.get(transport_type)
            if adapter is None:
                continue
            timer = observability_registry.start_timer()
            try:
                provider_segments = await adapter.fetch_segments(query)
                observability_registry.record_provider_call(
                    provider=adapter.provider_name,
                    latency_ms=timer(),
                    is_error=False,
                )
                logger.info(
                    "Provider segments fetched",
                    extra={
                        "provider": adapter.provider_name,
                        "transport_type": adapter.transport_type.value,
                        "segments_count": len(provider_segments),
                        "origin_id": query.origin_id,
                        "destination_id": query.destination_id,
                        "date": query.date.isoformat(),
                    },
                )
                segments.extend(provider_segments)
            except Exception:
                observability_registry.record_provider_call(
                    provider=adapter.provider_name,
                    latency_ms=timer(),
                    is_error=True,
                )
                logger.exception(
                    "Provider fetch failed",
                    extra={
                        "provider": adapter.provider_name,
                        "transport_type": adapter.transport_type.value,
                        "origin_id": query.origin_id,
                        "destination_id": query.destination_id,
                        "date": query.date.isoformat(),
                    },
                )
                raise
        return segments
