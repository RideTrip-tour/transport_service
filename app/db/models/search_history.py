from __future__ import annotations

import datetime as dt

from sqlalchemy import CheckConstraint, Date, DateTime, Index, Integer, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base


class SearchHistory(Base):
    __tablename__ = "search_history"
    __table_args__ = (
        Index("ix_search_history_user_created", "user_id", "created_at"),
        Index(
            "ix_search_history_origin_destination_date",
            "origin_location_id",
            "destination_location_id",
            "date",
        ),
        Index("ix_search_history_created_at", "created_at"),
        CheckConstraint(
            "origin_location_id <> destination_location_id",
            name="ck_search_history_origin_neq_destination",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    origin_location_id: Mapped[int] = mapped_column(Integer, nullable=False)
    destination_location_id: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    preferences: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
