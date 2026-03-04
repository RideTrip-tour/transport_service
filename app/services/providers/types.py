from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from app.schemas.routes_api import TransportType


@dataclass(slots=True, frozen=True)
class SegmentSearchQuery:
    origin_id: int
    destination_id: int
    date: date
    top_n: int
    trace_id: str | None = None


@dataclass(slots=True, frozen=True)
class ProviderSegment:
    provider: str
    transport_type: TransportType
    external_id: str
    origin_hub_id: int
    destination_hub_id: int
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int
    price_amount: Decimal
    currency: str
    raw_payload: dict | None = None

