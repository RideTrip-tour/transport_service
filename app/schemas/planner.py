from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import OptimizationMode


class ComposeRouteRequest(BaseModel):
    from_location_id: int = Field(gt=0)
    to_location_id: int = Field(gt=0)
    optimization: OptimizationMode = OptimizationMode.FASTEST
    allowed_transport_type_ids: list[int] | None = None


class RouteSegment(BaseModel):
    route_id: int
    transport_type_id: int
    from_location_id: int
    to_location_id: int
    duration_minutes: int
    price_amount: Decimal | None = None
    currency: str | None = None


class ComposeRouteResponse(BaseModel):
    total_duration_minutes: int
    total_price_amount: Decimal | None = Field(default=None, ge=0)
    currency: str | None = None
    transfers: int
    segments: list[RouteSegment]
