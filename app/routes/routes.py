from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.errors import ExternalDependencyAppError, ValidationAppError
from app.schemas.api_error import ApiErrorResponse
from app.schemas.routes_api import (
    RouteBatchRecalculateRequest,
    RouteBatchRecalculateResponse,
    RouteRecalculateRequest,
    RouteRecalculateResponse,
    RouteSearchRequest,
    RouteSearchResponse,
)
from app.services.location_client import LocationClient, LocationServiceUnavailableError
from app.services.route_application import DbRouteApplicationService

router = APIRouter(prefix="/routes", tags=["routes"])
route_service = DbRouteApplicationService()
location_client = LocationClient()

ERROR_RESPONSES = {
    413: {"model": ApiErrorResponse},
    404: {"model": ApiErrorResponse},
    422: {"model": ApiErrorResponse},
    503: {"model": ApiErrorResponse},
    504: {"model": ApiErrorResponse},
}


def _extract_user_id(request: Request) -> int | None:
    """Extract authenticated user id from gateway middleware payload."""
    user_data = getattr(request.state, "user_data", None)
    if not isinstance(user_data, dict):
        return None

    for key in ("user_id", "id", "sub"):
        value = user_data.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None


async def _validate_locations(origin_id: int, destination_id: int) -> None:
    """Validate route endpoints against location-service."""
    try:
        origin_exists = await location_client.ensure_location_exists(origin_id)
        destination_exists = await location_client.ensure_location_exists(destination_id)
    except LocationServiceUnavailableError as exc:
        raise ExternalDependencyAppError(
            message="Location service unavailable",
            details={"error": str(exc)},
        ) from exc

    if not origin_exists or not destination_exists:
        raise ValidationAppError(
            message="Unknown departure or arrival location",
            details={
                "origin_id": origin_id,
                "destination_id": destination_id,
                "origin_exists": origin_exists,
                "destination_exists": destination_exists,
            },
        )


@router.post("/search", response_model=RouteSearchResponse, responses=ERROR_RESPONSES)
async def search_routes(
    request: Request,
    payload: RouteSearchRequest,
    session: AsyncSession = Depends(get_async_session),
) -> RouteSearchResponse:
    """Search top-N routes for given locations and date."""
    await _validate_locations(payload.origin_id, payload.destination_id)
    return await route_service.search(
        session=session,
        payload=payload,
        user_id=_extract_user_id(request),
        trace_id=getattr(request.state, "trace_id", None),
    )


@router.post(
    "/{route_id}/recalculate",
    response_model=RouteRecalculateResponse,
    responses=ERROR_RESPONSES,
)
async def recalculate_route(
    request: Request,
    route_id: int,
    payload: RouteRecalculateRequest,
    session: AsyncSession = Depends(get_async_session),
) -> RouteRecalculateResponse:
    """Recalculate a previously persisted route."""
    idempotency_key = request.headers.get("Idempotency-Key")
    return await route_service.recalculate(
        session=session,
        route_id=route_id,
        payload=payload,
        idempotency_key=idempotency_key,
    )


@router.post(
    "/batch-recalculate",
    response_model=RouteBatchRecalculateResponse,
    responses=ERROR_RESPONSES,
)
async def batch_recalculate_routes(
    payload: RouteBatchRecalculateRequest,
    session: AsyncSession = Depends(get_async_session),
) -> RouteBatchRecalculateResponse:
    """Run synchronous batch recalculation request."""
    return await route_service.batch_recalculate(session=session, payload=payload)


@router.post(
    "/batch-recalculate/trigger",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=RouteBatchRecalculateResponse,
    responses=ERROR_RESPONSES,
)
async def trigger_batch_recalculate(
    payload: RouteBatchRecalculateRequest,
    session: AsyncSession = Depends(get_async_session),
) -> RouteBatchRecalculateResponse:
    """Handle external trigger (cron/notification service) for batch recalculation."""
    return await route_service.batch_recalculate(session=session, payload=payload)
