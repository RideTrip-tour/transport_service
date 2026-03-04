from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(slots=True, frozen=True)
class Segment:
    provider: str
    transport_type: str
    external_id: str
    origin_hub_id: int
    destination_hub_id: int
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int
    price_amount: Decimal
    currency: str
    payment_url: str | None


@dataclass(slots=True, frozen=True)
class Route:
    route_id: int
    route_version: int
    origin_id: int
    destination_id: int
    date: date
    total_price: Decimal
    currency: str
    total_duration_minutes: int
    total_transfer_duration_minutes: int
    transfers_count: int
    score: float
    segments: tuple[Segment, ...]


@dataclass(slots=True, frozen=True)
class SearchHistoryEntry:
    user_id: int
    origin_id: int
    destination_id: int
    date: date
    preferences: dict
    created_at: datetime


@dataclass(slots=True, frozen=True)
class ProviderQuote:
    provider: str
    price_amount: Decimal
    currency: str
    payment_url: str
    expires_at: datetime | None

