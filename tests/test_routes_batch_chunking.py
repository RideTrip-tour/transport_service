import pytest

from app.schemas.routes_api import RouteBatchRecalculateRequest
from app.services.route_application import DbRouteApplicationService


@pytest.mark.asyncio
async def test_batch_recalculate_reads_routes_in_chunks(monkeypatch, db_session_factory):
    service = DbRouteApplicationService()
    calls: list[int] = []

    async def fake_list_by_ids(session, route_ids):  # noqa: ARG001
        calls.append(len(route_ids))
        return []

    monkeypatch.setattr(
        "app.services.route_application.RouteCrud.list_by_ids",
        fake_list_by_ids,
    )

    payload = RouteBatchRecalculateRequest(
        route_ids=list(range(1, 251)),
        force_refresh=True,
    )

    async with db_session_factory() as session:
        result = await service.batch_recalculate(session=session, payload=payload)

    assert result.total == 250
    assert result.failed == 250
    assert calls == [100, 100, 50]

