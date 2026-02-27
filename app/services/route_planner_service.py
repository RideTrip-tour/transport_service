import heapq
import logging
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.transport_catalog_crud import TransportCatalogCrud
from app.db.models import TransportCatalogRoute
from app.schemas.common import OptimizationMode
from app.schemas.planner import ComposeRouteResponse, RouteSegment


class RouteNotFoundError(Exception):
    pass


logger = logging.getLogger("app.route_planner")


class RoutePlannerService:
    @staticmethod
    def _weight(route: TransportCatalogRoute, optimization: OptimizationMode) -> float:
        if optimization == OptimizationMode.FASTEST:
            return float(route.base_duration_minutes)
        if optimization == OptimizationMode.CHEAPEST:
            return float(route.base_price_amount or Decimal("999999.0"))

        price = float(route.base_price_amount or Decimal("1000"))
        duration = float(route.base_duration_minutes)
        return duration * 0.65 + price * 0.35

    async def compose(
        self,
        session: AsyncSession,
        from_location_id: int,
        to_location_id: int,
        optimization: OptimizationMode,
        allowed_transport_type_ids: list[int] | None = None,
    ) -> ComposeRouteResponse:
        routes = await TransportCatalogCrud.list(session=session, is_active=True)
        if allowed_transport_type_ids:
            allowed = set(allowed_transport_type_ids)
            routes = [route for route in routes if route.transport_type_id in allowed]
        logger.info(
            "Planner input loaded",
            extra={
                "from_location_id": from_location_id,
                "to_location_id": to_location_id,
                "routes_count": len(routes),
                "optimization": optimization.value,
            },
        )

        adjacency: dict[int, list[TransportCatalogRoute]] = {}
        for route in routes:
            adjacency.setdefault(route.from_location_id, []).append(route)

        serial = 0
        pq: list[tuple[float, int, int]] = [(0.0, serial, from_location_id)]
        dist: dict[int, float] = {from_location_id: 0.0}
        prev: dict[int, TransportCatalogRoute] = {}

        while pq:
            score, _, node = heapq.heappop(pq)
            if node == to_location_id:
                break
            if score > dist.get(node, float("inf")):
                continue

            for edge in adjacency.get(node, []):
                next_node = edge.to_location_id
                new_score = score + self._weight(edge, optimization)
                if new_score < dist.get(next_node, float("inf")):
                    dist[next_node] = new_score
                    prev[next_node] = edge
                    serial += 1
                    heapq.heappush(pq, (new_score, serial, next_node))

        if to_location_id not in dist:
            logger.warning(
                "Planner route not found",
                extra={
                    "from_location_id": from_location_id,
                    "to_location_id": to_location_id,
                },
            )
            raise RouteNotFoundError("No route found for requested locations")

        path: list[TransportCatalogRoute] = []
        cur = to_location_id
        while cur != from_location_id:
            edge = prev[cur]
            path.append(edge)
            cur = edge.from_location_id
        path.reverse()

        total_duration = sum(item.base_duration_minutes for item in path)
        total_price = sum(item.base_price_amount or Decimal("0") for item in path)
        currencies = {item.base_currency for item in path if item.base_currency}
        currency = next(iter(currencies), None) if len(currencies) <= 1 else None

        segments = [
            RouteSegment(
                route_id=item.id,
                transport_type_id=item.transport_type_id,
                from_location_id=item.from_location_id,
                to_location_id=item.to_location_id,
                duration_minutes=item.base_duration_minutes,
                price_amount=item.base_price_amount,
                currency=item.base_currency,
            )
            for item in path
        ]

        result = ComposeRouteResponse(
            total_duration_minutes=total_duration,
            total_price_amount=total_price if total_price > 0 else None,
            currency=currency,
            transfers=max(len(path) - 1, 0),
            segments=segments,
        )
        logger.info(
            "Planner route composed",
            extra={
                "from_location_id": from_location_id,
                "to_location_id": to_location_id,
                "segments_count": len(segments),
                "total_duration_minutes": total_duration,
                "transfers": result.transfers,
            },
        )
        return result
