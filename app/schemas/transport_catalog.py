from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TransportCatalogRouteCreate(BaseModel):
    transport_type_id: int = Field(gt=0)
    from_location_id: int = Field(gt=0)
    to_location_id: int = Field(gt=0)
    base_duration_minutes: int = Field(gt=0)
    base_price_amount: Decimal | None = Field(default=None, ge=0)
    base_currency: str | None = Field(default=None, min_length=3, max_length=3)
    provider: str | None = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def validate_locations_not_equal(self) -> "TransportCatalogRouteCreate":
        if self.from_location_id == self.to_location_id:
            raise ValueError("from_location_id must not be equal to to_location_id")
        return self


class TransportCatalogRouteUpdate(BaseModel):
    transport_type_id: int | None = Field(default=None, gt=0)
    from_location_id: int | None = Field(default=None, gt=0)
    to_location_id: int | None = Field(default=None, gt=0)
    base_duration_minutes: int | None = Field(default=None, gt=0)
    base_price_amount: Decimal | None = Field(default=None, ge=0)
    base_currency: str | None = Field(default=None, min_length=3, max_length=3)
    provider: str | None = Field(default=None, max_length=128)
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_locations_not_equal(self) -> "TransportCatalogRouteUpdate":
        if (
            self.from_location_id is not None
            and self.to_location_id is not None
            and self.from_location_id == self.to_location_id
        ):
            raise ValueError("from_location_id must not be equal to to_location_id")
        return self


class TransportCatalogRouteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transport_type_id: int
    from_location_id: int
    to_location_id: int
    base_duration_minutes: int
    base_price_amount: Decimal | None
    base_currency: str | None
    provider: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
