import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.schemas.planner import ComposeRouteRequest, ComposeRouteResponse
from app.services.location_client import LocationClient, LocationServiceUnavailableError
from app.services.route_planner_service import RouteNotFoundError, RoutePlannerService

router = APIRouter(prefix="/planner", tags=["transport-planner"])
planner_service = RoutePlannerService()
location_client = LocationClient()
logger = logging.getLogger("app.route_planner_api")


@router.post("/compose", response_model=ComposeRouteResponse)
async def compose_route(
    payload: ComposeRouteRequest,
    session: AsyncSession = Depends(get_async_session),
) -> ComposeRouteResponse:
    """Построить составной маршрут между двумя локациями."""
    logger.info(
        "Compose route request",
        extra={
            "from_location_id": payload.from_location_id,
            "to_location_id": payload.to_location_id,
            "optimization": payload.optimization.value,
        },
    )
    try:
        from_exists = await location_client.ensure_location_exists(
            payload.from_location_id
        )
        to_exists = await location_client.ensure_location_exists(payload.to_location_id)
    except LocationServiceUnavailableError as exc:
        raise HTTPException(
            status_code=503, detail=f"Location service unavailable: {exc}"
        ) from exc

    if not from_exists or not to_exists:
        logger.warning(
            "Unknown location in compose request",
            extra={"from_exists": from_exists, "to_exists": to_exists},
        )
        raise HTTPException(
            status_code=422, detail="Unknown departure or arrival location"
        )

    try:
        result = await planner_service.compose(
            session=session,
            from_location_id=payload.from_location_id,
            to_location_id=payload.to_location_id,
            optimization=payload.optimization,
            allowed_transport_type_ids=payload.allowed_transport_type_ids,
        )
        logger.info(
            "Compose route success", extra={"segments_count": len(result.segments)}
        )
        return result
    except RouteNotFoundError as exc:
        logger.warning("Compose route failed: no route found")
        raise HTTPException(status_code=404, detail=str(exc)) from exc
