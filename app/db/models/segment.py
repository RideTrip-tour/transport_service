from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class Segment(TimestampMixin, Base):
    __tablename__ = "segments"
    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_segments_provider_external_id"),
        Index(
            "ix_segments_origin_destination_departure",
            "origin_hub_id",
            "destination_hub_id",
            "departure_time",
        ),
        Index("ix_segments_expires_at", "expires_at"),
        CheckConstraint(
            "origin_hub_id <> destination_hub_id",
            name="ck_segments_origin_neq_destination",
        ),
        CheckConstraint(
            "arrival_time > departure_time",
            name="ck_segments_arrival_gt_departure",
        ),
        CheckConstraint("price_amount >= 0", name="ck_segments_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(128), nullable=False)
    transport_type: Mapped[str] = mapped_column(String(32), nullable=False)
    origin_hub_id: Mapped[int] = mapped_column(Integer, nullable=False)
    destination_hub_id: Mapped[int] = mapped_column(Integer, nullable=False)
    departure_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    arrival_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

