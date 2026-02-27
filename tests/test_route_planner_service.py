from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.crud.transport_catalog_crud import TransportCatalogCrud
from app.schemas.common import OptimizationMode
from app.services.route_planner_service import RouteNotFoundError, RoutePlannerService


def _route(
    *,
    transport_type_id,
    from_location_id,
    to_location_id,
    duration,
    price,
    currency="USD",
):
    return SimpleNamespace(
        id=(from_location_id * 1000) + to_location_id,
        transport_type_id=transport_type_id,
        from_location_id=from_location_id,
        to_location_id=to_location_id,
        base_duration_minutes=duration,
        base_price_amount=Decimal(price) if price is not None else None,
        base_currency=currency,
    )


@pytest.mark.asyncio
async def test_compose_fastest_selects_shorter_total_duration(monkeypatch):
    service = RoutePlannerService()
    t1 = 1
    a, b, c = 10, 20, 30
    routes = [
        _route(
            transport_type_id=t1,
            from_location_id=a,
            to_location_id=c,
            duration=150,
            price="10",
        ),
        _route(
            transport_type_id=t1,
            from_location_id=a,
            to_location_id=b,
            duration=60,
            price="40",
        ),
        _route(
            transport_type_id=t1,
            from_location_id=b,
            to_location_id=c,
            duration=60,
            price="40",
        ),
    ]

    async def fake_list(*args, **kwargs):  # noqa: ARG001
        return routes

    monkeypatch.setattr(TransportCatalogCrud, "list", fake_list)

    result = await service.compose(
        session=None,
        from_location_id=a,
        to_location_id=c,
        optimization=OptimizationMode.FASTEST,
    )

    assert result.total_duration_minutes == 120
    assert result.transfers == 1
    assert len(result.segments) == 2


@pytest.mark.asyncio
async def test_compose_cheapest_selects_lowest_total_price(monkeypatch):
    service = RoutePlannerService()
    t1 = 1
    a, b, c = 10, 20, 30
    routes = [
        _route(
            transport_type_id=t1,
            from_location_id=a,
            to_location_id=c,
            duration=60,
            price="100",
        ),
        _route(
            transport_type_id=t1,
            from_location_id=a,
            to_location_id=b,
            duration=70,
            price="25",
        ),
        _route(
            transport_type_id=t1,
            from_location_id=b,
            to_location_id=c,
            duration=70,
            price="25",
        ),
    ]

    async def fake_list(*args, **kwargs):  # noqa: ARG001
        return routes

    monkeypatch.setattr(TransportCatalogCrud, "list", fake_list)

    result = await service.compose(
        session=None,
        from_location_id=a,
        to_location_id=c,
        optimization=OptimizationMode.CHEAPEST,
    )

    assert result.total_price_amount == Decimal("50")
    assert result.transfers == 1
    assert len(result.segments) == 2


@pytest.mark.asyncio
async def test_compose_raises_when_path_not_found(monkeypatch):
    service = RoutePlannerService()
    t1 = 1
    a, b, c = 10, 20, 30
    routes = [
        _route(
            transport_type_id=t1,
            from_location_id=a,
            to_location_id=b,
            duration=50,
            price="10",
        )
    ]

    async def fake_list(*args, **kwargs):  # noqa: ARG001
        return routes

    monkeypatch.setattr(TransportCatalogCrud, "list", fake_list)

    with pytest.raises(RouteNotFoundError):
        await service.compose(
            session=None,
            from_location_id=a,
            to_location_id=c,
            optimization=OptimizationMode.FASTEST,
        )
