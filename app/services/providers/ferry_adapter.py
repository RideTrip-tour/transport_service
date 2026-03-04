from app.schemas.routes_api import TransportType
from app.services.providers.base import ProviderAdapter
from app.services.providers.types import ProviderSegment, SegmentSearchQuery


class FerryProviderAdapter(ProviderAdapter):
    @property
    def transport_type(self) -> TransportType:
        return TransportType.FERRY

    @property
    def provider_name(self) -> str:
        return "ferry_provider"

    async def fetch_segments(self, query: SegmentSearchQuery) -> list[ProviderSegment]:
        _ = query
        return []

