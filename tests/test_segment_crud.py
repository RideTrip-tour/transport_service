from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.crud.segment_crud import SegmentCrud


@pytest.mark.asyncio
async def test_segment_create_list_and_delete_expired(db_session_factory):
    async with db_session_factory() as session:
        now = datetime.now(timezone.utc)
        await SegmentCrud.create_many(
            session=session,
            items=[
                {
                    "provider": "stub",
                    "transport_type": "flight",
                    "origin_hub_id": 10,
                    "destination_hub_id": 20,
                    "departure_time": now + timedelta(hours=1),
                    "arrival_time": now + timedelta(hours=2),
                    "price_amount": Decimal("50.00"),
                    "currency": "USD",
                    "external_id": "seg-1",
                    "raw_payload": {"a": 1},
                    "expires_at": now + timedelta(minutes=30),
                },
                {
                    "provider": "stub",
                    "transport_type": "flight",
                    "origin_hub_id": 10,
                    "destination_hub_id": 20,
                    "departure_time": now + timedelta(hours=3),
                    "arrival_time": now + timedelta(hours=4),
                    "price_amount": Decimal("60.00"),
                    "currency": "USD",
                    "external_id": "seg-2",
                    "raw_payload": {"a": 2},
                    "expires_at": now - timedelta(minutes=30),
                },
            ],
        )
        rows = await SegmentCrud.list_by_direction_date(
            session=session,
            origin_hub_id=10,
            destination_hub_id=20,
            departure_date=now.date(),
        )
        assert len(rows) >= 1

        deleted = await SegmentCrud.delete_expired(session)
        assert deleted >= 1
