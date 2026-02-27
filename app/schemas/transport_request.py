from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.schemas.common import RequestStatus, RequestType


class TransportRequestCreate(BaseModel):
    user_id: int = Field(gt=0)
    type: RequestType = RequestType.COMPOSED
    transport_type_id: int | None = Field(default=None, gt=0)
    departure_datetime: datetime | None = None
    arrival_datetime: datetime | None = None
    departure_location_id: int = Field(gt=0)
    arrival_location_id: int = Field(gt=0)
    passenger_count: int = Field(gt=0)
    comment: str | None = Field(default=None, max_length=512)


class TransportRequestUpdate(BaseModel):
    type: RequestType | None = None
    status: RequestStatus | None = None
    transport_type_id: int | None = Field(default=None, gt=0)
    departure_datetime: datetime | None = None
    arrival_datetime: datetime | None = None
    departure_location_id: int | None = Field(default=None, gt=0)
    arrival_location_id: int | None = Field(default=None, gt=0)
    passenger_count: int | None = Field(default=None, gt=0)
    comment: str | None = Field(default=None, max_length=512)


class TransportRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    type: str
    status: str
    transport_type_id: int | None
    departure_datetime: datetime | None
    arrival_datetime: datetime | None
    departure_location_id: int
    arrival_location_id: int
    passenger_count: int
    comment: str | None
    created_at: datetime
    updated_at: datetime


class TransportQuoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transport_request_id: int
    provider_name: str
    external_quote_id: str | None
    price_amount: float
    currency: str
    payment_url: HttpUrl
    expires_at: datetime | None
    payload: dict | None
    created_at: datetime
    updated_at: datetime
