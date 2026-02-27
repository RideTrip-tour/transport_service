import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.transport_catalog_crud import TransportCatalogCrud
from app.db.database import get_async_session
from app.schemas.transport_catalog import (
    TransportCatalogRouteCreate,
    TransportCatalogRouteRead,
    TransportCatalogRouteUpdate,
)
from app.services.location_client import LocationClient, LocationServiceUnavailableError

router = APIRouter(prefix="/catalog/routes", tags=["transport-catalog"])
location_client = LocationClient()
logger = logging.getLogger("app.transport_catalog")


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
    "", response_model=TransportCatalogRouteRead, status_code=status.HTTP_201_CREATED
)
async def create_catalog_route(
    payload: TransportCatalogRouteCreate,
    session: AsyncSession = Depends(get_async_session),
) -> TransportCatalogRouteRead:
    """Создать маршрут в каталоге доступных транспортных сегментов."""
    logger.info(
        "Create catalog route request",
        extra={
            "transport_type_id": payload.transport_type_id,
            "from_location_id": payload.from_location_id,
            "to_location_id": payload.to_location_id,
        },
    )
    await _validate_locations(payload.from_location_id, payload.to_location_id)
    item = await TransportCatalogCrud.create(session, payload)
    logger.info("Catalog route created", extra={"route_id": item.id})
    return TransportCatalogRouteRead.model_validate(item)


@router.get("", response_model=list[TransportCatalogRouteRead])
async def list_catalog_routes(
    from_location_id: int | None = Query(default=None, gt=0),
    to_location_id: int | None = Query(default=None, gt=0),
    transport_type_id: int | None = Query(default=None, gt=0),
    is_active: bool | None = Query(default=True),
    session: AsyncSession = Depends(get_async_session),
) -> list[TransportCatalogRouteRead]:
    """Получить список маршрутов каталога с фильтрацией по параметрам."""
    items = await TransportCatalogCrud.list(
        session=session,
        from_location_id=from_location_id,
        to_location_id=to_location_id,
        transport_type_id=transport_type_id,
        is_active=is_active,
    )
    logger.info("Catalog routes listed", extra={"count": len(items)})
    return [TransportCatalogRouteRead.model_validate(item) for item in items]


@router.get("/{item_id}", response_model=TransportCatalogRouteRead)
async def get_catalog_route(
    item_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> TransportCatalogRouteRead:
    """Получить маршрут каталога по идентификатору."""
    item = await TransportCatalogCrud.get(session, item_id)
    if not item:
        logger.warning("Catalog route not found", extra={"route_id": item_id})
        raise HTTPException(status_code=404, detail="Catalog route not found")
    return TransportCatalogRouteRead.model_validate(item)


@router.patch("/{item_id}", response_model=TransportCatalogRouteRead)
async def update_catalog_route(
    item_id: int,
    payload: TransportCatalogRouteUpdate,
    session: AsyncSession = Depends(get_async_session),
) -> TransportCatalogRouteRead:
    """Обновить маршрут каталога."""
    item = await TransportCatalogCrud.get(session, item_id)
    if not item:
        logger.warning(
            "Catalog route not found for update", extra={"route_id": item_id}
        )
        raise HTTPException(status_code=404, detail="Catalog route not found")

    from_location_id = payload.from_location_id or item.from_location_id
    to_location_id = payload.to_location_id or item.to_location_id
    await _validate_locations(from_location_id, to_location_id)

    updated = await TransportCatalogCrud.update(session, item, payload)
    logger.info("Catalog route updated", extra={"route_id": item_id})
    return TransportCatalogRouteRead.model_validate(updated)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_catalog_route(
    item_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Мягко удалить маршрут каталога (деактивировать запись)."""
    item = await TransportCatalogCrud.get(session, item_id)
    if not item:
        logger.warning(
            "Catalog route not found for delete", extra={"route_id": item_id}
        )
        raise HTTPException(status_code=404, detail="Catalog route not found")
    await TransportCatalogCrud.update(
        session=session,
        item=item,
        data=TransportCatalogRouteUpdate(is_active=False),
    )
    logger.info("Catalog route deactivated", extra={"route_id": item_id})
