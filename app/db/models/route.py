from __future__ import annotations

import datetime as dt
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class Route(TimestampMixin, Base):
    __tablename__ = "routes"
    __table_args__ = (
        Index(
            "ix_routes_origin_destination_date",
            "origin_location_id",
            "destination_location_id",
            "date",
        ),
        Index("ix_routes_date", "date"),
        Index("ix_routes_updated_at", "updated_at"),
        CheckConstraint(
            "origin_location_id <> destination_location_id",
            name="ck_routes_origin_neq_destination",
        ),
        CheckConstraint("total_price >= 0", name="ck_routes_total_price_non_negative"),
        CheckConstraint(
            "total_duration_minutes > 0",
            name="ck_routes_total_duration_positive",
        ),
        CheckConstraint(
            "total_transfer_duration_minutes >= 0",
            name="ck_routes_transfer_duration_non_negative",
        ),
        CheckConstraint(
            "transfers_count >= 0",
            name="ck_routes_transfers_count_non_negative",
        ),
        CheckConstraint("route_version >= 1", name="ck_routes_version_min_1"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    route_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    origin_location_id: Mapped[int] = mapped_column(Integer, nullable=False)
    destination_location_id: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    total_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    total_transfer_duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    transfers_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    segments_snapshot: Mapped[list[dict]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
    )
    recalculated_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
