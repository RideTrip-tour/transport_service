from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class TransportQuote(TimestampMixin, Base):
    __tablename__ = "transport_quotes"
    __table_args__ = (
        Index("ix_transport_quotes_transport_request_id", "transport_request_id"),
        Index("ix_transport_quotes_currency", "currency"),
        Index("ix_transport_quotes_provider_name", "provider_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transport_request_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("transport_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider_name: Mapped[str] = mapped_column(String(128), nullable=False)
    external_quote_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    payment_url: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
