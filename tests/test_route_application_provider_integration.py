from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.db.models import Route, Segment
from app.schemas.routes_api import RoutePreferences, RouteSearchRequest, TransportType
from app.services.providers import ProviderRegistry, SegmentSearchQuery
from app.services.providers.base import ProviderAdapter
from app.services.providers.types import ProviderSegment
from app.services.route_application import DbRouteApplicationService


class _FlightAdapterForServiceTest(ProviderAdapter):
    @property
    def transport_type(self) -> TransportType:
        return TransportType.FLIGHT

    @property
    def provider_name(self) -> str:
        return "flight_test_provider"

    async def fetch_segments(self, query: SegmentSearchQuery) -> list[ProviderSegment]:
        return [
            ProviderSegment(
                provider=self.provider_name,
                transport_type=TransportType.FLIGHT,
                external_id=f"provider-seg-{idx}",
                origin_hub_id=query.origin_id,
                destination_hub_id=query.destination_id,
                departure_time=datetime(2026, 4, 1, 10 + idx, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2026, 4, 1, 11 + idx, 30, tzinfo=timezone.utc),
                duration_minutes=90,
                price_amount=Decimal("40.00") + Decimal(idx),
                currency="USD",
                raw_payload={"provider_case": "ok"},
            )
            for idx in range(query.top_n)
        ]


@pytest.mark.asyncio
async def test_search_uses_provider_registry_and_persists_segments(db_session_factory):
    service = DbRouteApplicationService(
        provider_registry=ProviderRegistry([_FlightAdapterForServiceTest(max_concurrency=1)])
    )
    request = RouteSearchRequest(
        origin_id=10,
        destination_id=20,
        date=date(2026, 4, 1),
        top_n=2,
        preferences=RoutePreferences(transport_types=[TransportType.FLIGHT]),
    )

    async with db_session_factory() as session:
        result = await service.search(session=session, payload=request, user_id=5)
        assert len(result.routes) == 2
        assert result.routes[0].segments[0].provider == "flight_test_provider"

        stored_routes = list((await session.execute(select(Route))).scalars().all())
        stored_segments = list((await session.execute(select(Segment))).scalars().all())
        assert len(stored_routes) == 2
        assert len(stored_segments) == 2
        assert stored_segments[0].provider == "flight_test_provider"

