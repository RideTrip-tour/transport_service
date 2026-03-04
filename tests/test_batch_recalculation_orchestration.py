"""Tests for Epic 07 batch recalculation orchestration."""

from datetime import date
from decimal import Decimal

import pytest

from app.crud.route_crud import RouteCrud
from app.schemas.routes_api import RouteBatchRecalculateRequest
from app.services.route_application import DbRouteApplicationService


@pytest.mark.asyncio
async def test_batch_recalculate_returns_unchanged_when_force_refresh_false(db_session_factory):
    """Batch should mark existing routes as unchanged when refresh is disabled."""
    service = DbRouteApplicationService()
    async with db_session_factory() as session:
        route = await RouteCrud.create(
            session=session,
            data={
                "origin_location_id": 10,
                "destination_location_id": 20,
                "date": date(2026, 4, 1),
                "total_price": Decimal("25.00"),
                "currency": "USD",
                "total_duration_minutes": 80,
                "total_transfer_duration_minutes": 0,
                "transfers_count": 0,
                "score": Decimal("10.0000"),
                "segments_snapshot": [],
            },
        )

        result = await service.batch_recalculate(
            session=session,
            payload=RouteBatchRecalculateRequest(
                route_ids=[route.id],
                force_refresh=False,
            ),
        )

    assert result.batch_id is not None
    assert result.updated == 0
    assert result.unchanged == 1
    assert result.items[0].status == "unchanged"


@pytest.mark.asyncio
async def test_batch_recalculate_deduplicates_route_ids(db_session_factory):
    """Batch should process duplicated route ids only once."""
    service = DbRouteApplicationService()
    async with db_session_factory() as session:
        route = await RouteCrud.create(
            session=session,
            data={
                "origin_location_id": 1,
                "destination_location_id": 2,
                "date": date(2026, 4, 1),
                "total_price": Decimal("25.00"),
                "currency": "USD",
                "total_duration_minutes": 80,
                "total_transfer_duration_minutes": 0,
                "transfers_count": 0,
                "score": Decimal("10.0000"),
                "segments_snapshot": [],
            },
        )
        result = await service.batch_recalculate(
            session=session,
            payload=RouteBatchRecalculateRequest(
                route_ids=[route.id, route.id, route.id],
                force_refresh=True,
            ),
        )
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].status == "updated"


@pytest.mark.asyncio
async def test_batch_recalculate_marks_failed_on_update_exception(monkeypatch, db_session_factory):
    """Batch should continue and mark item as failed when route update raises error."""
    service = DbRouteApplicationService()
    async with db_session_factory() as session:
        route = await RouteCrud.create(
            session=session,
            data={
                "origin_location_id": 1,
                "destination_location_id": 2,
                "date": date(2026, 4, 1),
                "total_price": Decimal("25.00"),
                "currency": "USD",
                "total_duration_minutes": 80,
                "total_transfer_duration_minutes": 0,
                "transfers_count": 0,
                "score": Decimal("10.0000"),
                "segments_snapshot": [],
            },
        )

        async def _boom(*args, **kwargs):  # noqa: ARG001
            raise RuntimeError("update failed")

        monkeypatch.setattr(
            "app.services.route_application.RouteCrud.update_with_new_version",
            _boom,
        )

        result = await service.batch_recalculate(
            session=session,
            payload=RouteBatchRecalculateRequest(
                route_ids=[route.id],
                force_refresh=True,
            ),
        )
    assert result.failed == 1
    assert result.items[0].status == "failed"
    assert "update failed" in (result.items[0].error or "")

