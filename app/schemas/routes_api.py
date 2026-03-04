from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class SortMode(str, Enum):
    PRICE = "price"
    TIME = "time"
    BALANCED = "balanced"


class TransportType(str, Enum):
    FLIGHT = "flight"
    TRAIN = "train"
    BUS = "bus"
    FERRY = "ferry"


class RoutePreferences(BaseModel):
    transport_types: list[TransportType] | None = None
    max_total_duration_minutes: int | None = Field(default=None, gt=0)
    max_transfers: int | None = Field(default=None, ge=0, le=5)
    budget_amount: Decimal | None = Field(default=None, ge=0)
    budget_currency: str | None = Field(default=None, min_length=3, max_length=3)
    min_transfer_minutes: int = Field(default=20, ge=0, le=720)


class RouteSearchRequest(BaseModel):
    origin_id: int = Field(gt=0)
    destination_id: int = Field(gt=0)
    date: date
    top_n: int = Field(default=5, ge=1, le=20)
    sort_by: SortMode = SortMode.BALANCED
    preferences: RoutePreferences = Field(default_factory=RoutePreferences)

    @model_validator(mode="after")
    def validate_origin_destination(self) -> "RouteSearchRequest":
        if self.origin_id == self.destination_id:
            raise ValueError("origin_id must not be equal to destination_id")
        return self


class SegmentDTO(BaseModel):
    provider: str
    transport_type: TransportType
    external_id: str
    origin_hub_id: int = Field(gt=0)
    destination_hub_id: int = Field(gt=0)
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int = Field(gt=0)
    price_amount: Decimal = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    payment_url: str | None = None


class RouteDTO(BaseModel):
    route_id: int
    route_version: int = Field(ge=1)
    origin_id: int = Field(gt=0)
    destination_id: int = Field(gt=0)
    date: date
    total_price: Decimal = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    total_duration_minutes: int = Field(gt=0)
    total_transfer_duration_minutes: int = Field(ge=0)
    transfers_count: int = Field(ge=0)
    score: float = Field(ge=0)
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    segments: list[SegmentDTO]


class RouteSearchResponse(BaseModel):
    routes: list[RouteDTO]


class RouteRecalculateRequest(BaseModel):
    force_refresh: bool = True
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=128)


class RouteRecalculateResponse(BaseModel):
    route: RouteDTO
    recalculated_at: datetime
    changed: bool


class RouteBatchRecalculateRequest(BaseModel):
    route_ids: list[int] = Field(min_length=1, max_length=500)
    force_refresh: bool = True
    max_concurrency: int = Field(default=5, ge=1, le=20)


class BatchRouteStatus(str, Enum):
    UPDATED = "updated"
    UNCHANGED = "unchanged"
    FAILED = "failed"
    NOT_FOUND = "not_found"


class RouteBatchRecalculateItem(BaseModel):
    route_id: int
    status: BatchRouteStatus
    route: RouteDTO | None = None
    error: str | None = None


class RouteBatchRecalculateResponse(BaseModel):
    batch_id: int | None = None
    total: int = Field(ge=0)
    updated: int = Field(ge=0)
    unchanged: int = Field(ge=0)
    failed: int = Field(ge=0)
    items: list[RouteBatchRecalculateItem]
