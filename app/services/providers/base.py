from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio

from config import settings

from app.schemas.routes_api import TransportType
from app.services.providers.types import ProviderSegment, SegmentSearchQuery


class ProviderAdapterError(Exception):
    pass


class ProviderAdapter(ABC):
    def __init__(self, max_concurrency: int = 10) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrency)

    @property
    @abstractmethod
    def transport_type(self) -> TransportType:
        raise NotImplementedError

    @property
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def fetch_segments(self, query: SegmentSearchQuery) -> list[ProviderSegment]:
        raise NotImplementedError

    @property
    def timeout_seconds(self) -> float:
        return settings.schedule_provider_timeout_ms / 1000

    @property
    def retries(self) -> int:
        return max(settings.schedule_provider_retries, 0)

