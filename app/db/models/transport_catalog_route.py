from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class TransportCatalogRoute(TimestampMixin, Base):
    __tablename__ = "transport_catalog_routes"
    __table_args__ = (
        Index("ix_catalog_routes_from_location_id", "from_location_id"),
        Index("ix_catalog_routes_to_location_id", "to_location_id"),
        Index("ix_catalog_routes_transport_type_id", "transport_type_id"),
        Index(
            "ix_catalog_routes_from_to_active",
            "from_location_id",
            "to_location_id",
            "is_active",
        ),
        CheckConstraint(
            "base_duration_minutes > 0", name="ck_catalog_route_duration_pos"
        ),
        CheckConstraint(
            "from_location_id <> to_location_id",
            name="ck_catalog_route_from_neq_to",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transport_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("transport_types.id", ondelete="RESTRICT"),
        nullable=False,
    )
    from_location_id: Mapped[int] = mapped_column(Integer, nullable=False)
    to_location_id: Mapped[int] = mapped_column(Integer, nullable=False)
    base_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    base_price_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    base_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
