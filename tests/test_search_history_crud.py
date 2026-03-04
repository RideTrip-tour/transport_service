from datetime import date

import pytest

from app.crud.search_history_crud import SearchHistoryCrud


@pytest.mark.asyncio
async def test_search_history_create_nullable_user_and_list(db_session_factory):
    async with db_session_factory() as session:
        await SearchHistoryCrud.create(
            session=session,
            data={
                "user_id": None,
                "origin_location_id": 10,
                "destination_location_id": 20,
                "date": date(2026, 4, 1),
                "preferences": {"transport_types": ["flight"]},
            },
        )
        await SearchHistoryCrud.create(
            session=session,
            data={
                "user_id": 77,
                "origin_location_id": 11,
                "destination_location_id": 22,
                "date": date(2026, 4, 2),
                "preferences": {"budget_amount": "50"},
            },
        )

        items = await SearchHistoryCrud.list_recent_by_user(session, user_id=77)
        assert len(items) == 1
        assert items[0].user_id == 77
        assert items[0].preferences["budget_amount"] == "50"

