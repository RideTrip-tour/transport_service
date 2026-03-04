from app.schemas.routes_api import TransportType
from app.services.providers.base import ProviderAdapter
from app.services.providers.types import ProviderSegment, SegmentSearchQuery


class TrainProviderAdapter(ProviderAdapter):
    @property
    def transport_type(self) -> TransportType:
        return TransportType.TRAIN

    @property
    def provider_name(self) -> str:
        return "train_provider"

    async def fetch_segments(self, query: SegmentSearchQuery) -> list[ProviderSegment]:
        _ = query
        return []

