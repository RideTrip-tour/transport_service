import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.transport_quote_crud import TransportQuoteCrud
from app.crud.transport_request_crud import TransportRequestCrud
from app.db.database import get_async_session
from app.schemas.common import RequestStatus
from app.schemas.transport_request import (
    TransportQuoteRead,
    TransportRequestCreate,
    TransportRequestRead,
    TransportRequestUpdate,
)
from app.services.location_client import LocationClient, LocationServiceUnavailableError
from app.services.schedule_provider_client import ScheduleProviderClient

router = APIRouter(prefix="/requests", tags=["transport-requests"])
location_client = LocationClient()
provider_client = ScheduleProviderClient()
logger = logging.getLogger("app.transport_requests")


async def _validate_locations(from_location_id: int, to_location_id: int) -> None:
    try:
        from_exists = await location_client.ensure_location_exists(from_location_id)
        to_exists = await location_client.ensure_location_exists(to_location_id)
    except LocationServiceUnavailableError as exc:
        raise HTTPException(
            status_code=503, detail=f"Location service unavailable: {exc}"
        ) from exc

    if not from_exists or not to_exists:
        raise HTTPException(
            status_code=422, detail="Unknown departure or arrival location"
        )


@router.post(
    "", response_model=TransportRequestRead, status_code=status.HTTP_201_CREATED
)
async def create_request(
    payload: TransportRequestCreate,
    session: AsyncSession = Depends(get_async_session),
) -> TransportRequestRead:
    """Создать пользовательский транспортный запрос."""
    logger.info(
        "Create transport request",
        extra={
            "user_id": payload.user_id,
            "departure_location_id": payload.departure_location_id,
            "arrival_location_id": payload.arrival_location_id,
        },
    )
    await _validate_locations(
        payload.departure_location_id, payload.arrival_location_id
    )
    item = await TransportRequestCrud.create(session, payload)
    logger.info(
        "Transport request created",
        extra={"request_id": item.id, "user_id": item.user_id},
    )
    return TransportRequestRead.model_validate(item)


@router.get("/{item_id}", response_model=TransportRequestRead)
async def get_request(
    item_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> TransportRequestRead:
    """Получить транспортный запрос по идентификатору."""
    item = await TransportRequestCrud.get(session, item_id)
    if not item:
        logger.warning("Transport request not found", extra={"request_id": item_id})
        raise HTTPException(status_code=404, detail="Transport request not found")
    return TransportRequestRead.model_validate(item)


@router.get("", response_model=list[TransportRequestRead])
async def list_requests(
    user_id: int = Query(..., gt=0),
    session: AsyncSession = Depends(get_async_session),
) -> list[TransportRequestRead]:
    """Получить список транспортных запросов пользователя."""
    items = await TransportRequestCrud.list_by_user(session, user_id)
    logger.info(
        "Transport requests listed", extra={"user_id": user_id, "count": len(items)}
    )
    return [TransportRequestRead.model_validate(item) for item in items]


@router.patch("/{item_id}", response_model=TransportRequestRead)
async def update_request(
    item_id: int,
    payload: TransportRequestUpdate,
    session: AsyncSession = Depends(get_async_session),
) -> TransportRequestRead:
    """Обновить параметры транспортного запроса."""
    item = await TransportRequestCrud.get(session, item_id)
    if not item:
        logger.warning(
            "Transport request not found for update", extra={"request_id": item_id}
        )
        raise HTTPException(status_code=404, detail="Transport request not found")

    from_location_id = payload.departure_location_id or item.departure_location_id
    to_location_id = payload.arrival_location_id or item.arrival_location_id
    await _validate_locations(from_location_id, to_location_id)

    updated = await TransportRequestCrud.update(session, item, payload)
    logger.info("Transport request updated", extra={"request_id": item_id})
    return TransportRequestRead.model_validate(updated)


@router.post("/{item_id}/quote", response_model=TransportQuoteRead)
async def quote_request(
    item_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> TransportQuoteRead:
    """Запросить оффер у внешнего провайдера и сохранить ссылку на оплату."""
    request_item = await TransportRequestCrud.get(session, item_id)
    if not request_item:
        logger.warning(
            "Transport request not found for quote", extra={"request_id": item_id}
        )
        raise HTTPException(status_code=404, detail="Transport request not found")

    total_duration = 60
    currency = None
    quote = await provider_client.get_quote_stub(
        request_id=item_id,
        total_duration_minutes=total_duration,
        base_currency=currency,
    )
    saved = await TransportQuoteCrud.create(
        session,
        transport_request_id=request_item.id,
        provider_name=quote.provider_name,
        external_quote_id=quote.external_quote_id,
        price_amount=quote.price_amount,
        currency=quote.currency,
        payment_url=quote.payment_url,
        expires_at=quote.expires_at,
        payload=quote.payload,
    )
    logger.info(
        "Quote saved",
        extra={
            "request_id": request_item.id,
            "quote_id": saved.id,
            "currency": saved.currency,
        },
    )

    await TransportRequestCrud.update(
        session,
        request_item,
        TransportRequestUpdate(status=RequestStatus.QUOTED),
    )

    return TransportQuoteRead.model_validate(saved)
