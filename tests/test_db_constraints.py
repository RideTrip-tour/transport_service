from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.crud.route_crud import RouteCrud


@pytest.mark.asyncio
async def test_route_constraint_rejects_negative_price(db_session_factory):
    async with db_session_factory() as session:
        with pytest.raises(IntegrityError):
            await RouteCrud.create(
                session=session,
                data={
                    "origin_location_id": 10,
                    "destination_location_id": 20,
                    "date": date(2026, 4, 1),
                    "total_price": Decimal("-1.00"),
                    "currency": "USD",
                    "total_duration_minutes": 120,
                    "total_transfer_duration_minutes": 0,
                    "transfers_count": 0,
                    "score": Decimal("10.0000"),
                    "segments_snapshot": [],
                },
            )


@pytest.mark.asyncio
async def test_route_constraint_rejects_non_positive_duration(db_session_factory):
    async with db_session_factory() as session:
        with pytest.raises(IntegrityError):
            await RouteCrud.create(
                session=session,
                data={
                    "origin_location_id": 10,
                    "destination_location_id": 20,
                    "date": date(2026, 4, 1),
                    "total_price": Decimal("1.00"),
                    "currency": "USD",
                    "total_duration_minutes": 0,
                    "total_transfer_duration_minutes": 0,
                    "transfers_count": 0,
                    "score": Decimal("10.0000"),
                    "segments_snapshot": [],
                },
            )
