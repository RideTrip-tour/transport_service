from datetime import date
from decimal import Decimal

import pytest

from app.crud.route_crud import RouteCrud


@pytest.mark.asyncio
async def test_route_create_get_update_version(db_session_factory):
    async with db_session_factory() as session:
        created = await RouteCrud.create(
            session=session,
            data={
                "origin_location_id": 10,
                "destination_location_id": 20,
                "date": date(2026, 4, 1),
                "total_price": Decimal("59.90"),
                "currency": "USD",
                "total_duration_minutes": 120,
                "total_transfer_duration_minutes": 0,
                "transfers_count": 0,
                "score": Decimal("99.1234"),
                "segments_snapshot": [
                    {
                        "provider": "stub",
                        "transport_type": "flight",
                        "external_id": "abc-1",
                        "origin_hub_id": 10,
                        "destination_hub_id": 20,
                        "departure_time": "2026-04-01T10:00:00Z",
                        "arrival_time": "2026-04-01T12:00:00Z",
                        "duration_minutes": 120,
                        "price_amount": "59.90",
                        "currency": "USD",
                        "payment_url": None,
                    }
                ],
            },
        )

        loaded = await RouteCrud.get(session, created.id)
        assert loaded is not None
        assert loaded.route_version == 1
        assert loaded.segments_snapshot[0]["external_id"] == "abc-1"

        updated = await RouteCrud.update_with_new_version(
            session=session,
            item=loaded,
            data={"score": Decimal("88.4321")},
        )
        assert updated.route_version == 2
        assert updated.recalculated_at is not None


@pytest.mark.asyncio
async def test_route_list_by_ids(db_session_factory):
    async with db_session_factory() as session:
        one = await RouteCrud.create(
            session=session,
            data={
                "origin_location_id": 1,
                "destination_location_id": 2,
                "date": date(2026, 4, 1),
                "total_price": Decimal("10.00"),
                "currency": "USD",
                "total_duration_minutes": 60,
                "total_transfer_duration_minutes": 0,
                "transfers_count": 0,
                "score": Decimal("10.0000"),
                "segments_snapshot": [],
            },
        )
        two = await RouteCrud.create(
            session=session,
            data={
                "origin_location_id": 3,
                "destination_location_id": 4,
                "date": date(2026, 4, 1),
                "total_price": Decimal("20.00"),
                "currency": "USD",
                "total_duration_minutes": 80,
                "total_transfer_duration_minutes": 0,
                "transfers_count": 0,
                "score": Decimal("20.0000"),
                "segments_snapshot": [],
            },
        )
        rows = await RouteCrud.list_by_ids(session, [one.id, two.id, 99999])
        assert sorted([item.id for item in rows]) == sorted([one.id, two.id])

