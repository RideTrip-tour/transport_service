from datetime import date, datetime, timezone
from decimal import Decimal

from app.schemas.routes_api import SegmentDTO, SortMode, TransportType
from app.services.routing_engine import RoutingConstraints, RoutingEngine


def _seg(
    *,
    external_id: str,
    origin: int,
    dest: int,
    dep_h: int,
    dep_m: int,
    arr_h: int,
    arr_m: int,
    price: str,
    transport_type: TransportType = TransportType.FLIGHT,
) -> SegmentDTO:
    dep = datetime(2026, 4, 1, dep_h, dep_m, tzinfo=timezone.utc)
    arr = datetime(2026, 4, 1, arr_h, arr_m, tzinfo=timezone.utc)
    return SegmentDTO(
        provider="test_provider",
        transport_type=transport_type,
        external_id=external_id,
        origin_hub_id=origin,
        destination_hub_id=dest,
        departure_time=dep,
        arrival_time=arr,
        duration_minutes=int((arr - dep).total_seconds() // 60),
        price_amount=Decimal(price),
        currency="USD",
        payment_url=None,
    )


def test_routing_engine_fastest_prefers_shorter_total_duration():
    engine = RoutingEngine()
    segments = [
        _seg(external_id="direct-slow", origin=1, dest=3, dep_h=9, dep_m=0, arr_h=12, arr_m=0, price="20"),
        _seg(external_id="a-b", origin=1, dest=2, dep_h=9, dep_m=0, arr_h=10, arr_m=0, price="15"),
        _seg(external_id="b-c", origin=2, dest=3, dep_h=10, dep_m=30, arr_h=11, arr_m=30, price="15"),
    ]
    routes = engine.find_routes(
        origin_id=1,
        destination_id=3,
        search_date=date(2026, 4, 1),
        segments=segments,
        sort_mode=SortMode.TIME,
        top_n=2,
        constraints=RoutingConstraints(min_transfer_minutes=20, max_transfers=3),
    )
    assert len(routes) >= 1
    assert [seg.external_id for seg in routes[0].segments] == ["a-b", "b-c"]


def test_routing_engine_cheapest_prefers_lower_price():
    engine = RoutingEngine()
    segments = [
        _seg(external_id="direct-expensive", origin=1, dest=3, dep_h=9, dep_m=0, arr_h=10, arr_m=0, price="120"),
        _seg(external_id="cheap-1", origin=1, dest=2, dep_h=9, dep_m=0, arr_h=9, arr_m=40, price="25"),
        _seg(external_id="cheap-2", origin=2, dest=3, dep_h=10, dep_m=10, arr_h=11, arr_m=0, price="25"),
    ]
    routes = engine.find_routes(
        origin_id=1,
        destination_id=3,
        search_date=date(2026, 4, 1),
        segments=segments,
        sort_mode=SortMode.PRICE,
        top_n=2,
        constraints=RoutingConstraints(min_transfer_minutes=20, max_transfers=3),
    )
    assert routes[0].total_price == Decimal("50")
    assert routes[0].transfers_count == 1


def test_routing_engine_respects_budget_and_transfer_constraints():
    engine = RoutingEngine()
    segments = [
        _seg(external_id="a-b", origin=1, dest=2, dep_h=9, dep_m=0, arr_h=10, arr_m=0, price="40"),
        _seg(external_id="b-c-too-tight", origin=2, dest=3, dep_h=10, dep_m=5, arr_h=11, arr_m=0, price="10"),
        _seg(external_id="b-c-ok", origin=2, dest=3, dep_h=10, dep_m=30, arr_h=11, arr_m=30, price="80"),
    ]
    routes = engine.find_routes(
        origin_id=1,
        destination_id=3,
        search_date=date(2026, 4, 1),
        segments=segments,
        sort_mode=SortMode.BALANCED,
        top_n=2,
        constraints=RoutingConstraints(
            min_transfer_minutes=20,
            max_transfers=2,
            budget_limit=Decimal("70"),
        ),
    )
    assert routes == []


def test_routing_engine_respects_allowed_transport_types_and_top_n():
    engine = RoutingEngine()
    segments = [
        _seg(external_id="flight-direct", origin=1, dest=3, dep_h=9, dep_m=0, arr_h=10, arr_m=0, price="60", transport_type=TransportType.FLIGHT),
        _seg(external_id="bus-direct", origin=1, dest=3, dep_h=9, dep_m=30, arr_h=11, arr_m=0, price="20", transport_type=TransportType.BUS),
        _seg(external_id="bus-direct-2", origin=1, dest=3, dep_h=12, dep_m=0, arr_h=13, arr_m=20, price="25", transport_type=TransportType.BUS),
    ]
    routes = engine.find_routes(
        origin_id=1,
        destination_id=3,
        search_date=date(2026, 4, 1),
        segments=segments,
        sort_mode=SortMode.PRICE,
        top_n=1,
        constraints=RoutingConstraints(
            min_transfer_minutes=20,
            max_transfers=1,
            allowed_transport_types={TransportType.BUS},
        ),
    )
    assert len(routes) == 1
    assert routes[0].segments[0].transport_type == TransportType.BUS

