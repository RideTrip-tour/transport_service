from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
import uuid

import httpx

from config import settings

from app.schemas.routes_api import TransportType
from app.services.providers.base import ProviderAdapter, ProviderAdapterError
from app.services.providers.types import ProviderSegment, SegmentSearchQuery


class FlightProviderAdapter(ProviderAdapter):
    @property
    def transport_type(self) -> TransportType:
        return TransportType.FLIGHT

    @property
    def provider_name(self) -> str:
        return "flight_provider"

    @property
    def _base_url(self) -> str:
        return settings.schedule_provider_base_url.rstrip("/")

    async def fetch_segments(self, query: SegmentSearchQuery) -> list[ProviderSegment]:
        try:
            payload = await self._request_segments(query)
            if not payload:
                return self._build_fallback_segments(query)
            return [self._map_segment(item) for item in payload[: query.top_n]]
        except Exception as exc:  # noqa: BLE001
            raise ProviderAdapterError(f"Flight provider failed: {exc}") from exc

    async def _request_segments(self, query: SegmentSearchQuery) -> list[dict[str, Any]]:
        if not self._base_url:
            return []

        url = f"{self._base_url}/flights/search"
        params = {
            "origin_id": query.origin_id,
            "destination_id": query.destination_id,
            "date": query.date.isoformat(),
            "limit": query.top_n,
        }
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                async with self._semaphore:
                    async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                        response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        return data
                    if isinstance(data, dict):
                        segments = data.get("segments", [])
                        if isinstance(segments, list):
                            return segments
                    raise ProviderAdapterError("Invalid flight provider payload format")
                last_error = ProviderAdapterError(
                    f"Unexpected response status {response.status_code}"
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
            if attempt < self.retries:
                await asyncio.sleep(0.2 * (2**attempt))
        if last_error:
            raise last_error
        return []

    def _map_segment(self, item: dict[str, Any]) -> ProviderSegment:
        departure = self._parse_dt(item.get("departure_time"))
        arrival = self._parse_dt(item.get("arrival_time"))
        duration = int((arrival - departure).total_seconds() // 60)
        return ProviderSegment(
            provider=str(item.get("provider") or self.provider_name),
            transport_type=TransportType.FLIGHT,
            external_id=str(item.get("external_id") or item.get("id") or uuid.uuid4()),
            origin_hub_id=int(item["origin_hub_id"]),
            destination_hub_id=int(item["destination_hub_id"]),
            departure_time=departure,
            arrival_time=arrival,
            duration_minutes=max(duration, 1),
            price_amount=Decimal(str(item["price_amount"])),
            currency=str(item.get("currency", "USD")).upper(),
            raw_payload=item,
        )

    def _build_fallback_segments(self, query: SegmentSearchQuery) -> list[ProviderSegment]:
        now = datetime.now(UTC)
        segments: list[ProviderSegment] = []
        for idx in range(query.top_n):
            departure = now + timedelta(hours=idx + 1)
            arrival = departure + timedelta(minutes=90 + idx * 15)
            segments.append(
                ProviderSegment(
                    provider=self.provider_name,
                    transport_type=TransportType.FLIGHT,
                    external_id=f"fallback-flight-{query.origin_id}-{query.destination_id}-{idx + 1}",
                    origin_hub_id=query.origin_id,
                    destination_hub_id=query.destination_id,
                    departure_time=departure,
                    arrival_time=arrival,
                    duration_minutes=int((arrival - departure).total_seconds() // 60),
                    price_amount=Decimal("45.00") + Decimal(idx * 7),
                    currency="USD",
                    raw_payload={"fallback": True},
                )
            )
        return segments

    @staticmethod
    def _parse_dt(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=UTC)
        if not value:
            raise ProviderAdapterError("Missing datetime field in provider payload")
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)

