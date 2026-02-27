from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class TransportRequest(TimestampMixin, Base):
    __tablename__ = "transport_requests"
    __table_args__ = (
        Index("ix_transport_requests_user_id", "user_id"),
        Index("ix_transport_requests_departure_location_id", "departure_location_id"),
        Index("ix_transport_requests_arrival_location_id", "arrival_location_id"),
        CheckConstraint(
            "passenger_count > 0", name="ck_transport_request_passenger_count_pos"
        ),
        CheckConstraint(
            "departure_location_id <> arrival_location_id",
            name="ck_transport_request_from_neq_to",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    transport_type_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("transport_types.id", ondelete="SET NULL"),
        nullable=True,
    )
    departure_datetime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    arrival_datetime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    departure_location_id: Mapped[int] = mapped_column(Integer, nullable=False)
    arrival_location_id: Mapped[int] = mapped_column(Integer, nullable=False)
    passenger_count: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(String(512), nullable=True)
