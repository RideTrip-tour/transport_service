from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TransportCatalogRoute
from app.schemas.transport_catalog import (
    TransportCatalogRouteCreate,
    TransportCatalogRouteUpdate,
)


class TransportCatalogCrud:
    @staticmethod
    async def create(
        session: AsyncSession,
        data: TransportCatalogRouteCreate,
    ) -> TransportCatalogRoute:
        item = TransportCatalogRoute(**data.model_dump())
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item

    @staticmethod
    async def list(
        session: AsyncSession,
        from_location_id: int | None = None,
        to_location_id: int | None = None,
        transport_type_id: int | None = None,
        is_active: bool | None = None,
    ) -> list[TransportCatalogRoute]:
        query = select(TransportCatalogRoute)
        if from_location_id:
            query = query.where(
                TransportCatalogRoute.from_location_id == from_location_id
            )
        if to_location_id:
            query = query.where(TransportCatalogRoute.to_location_id == to_location_id)
        if transport_type_id:
            query = query.where(
                TransportCatalogRoute.transport_type_id == transport_type_id
            )
        if is_active is not None:
            query = query.where(TransportCatalogRoute.is_active == is_active)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get(session: AsyncSession, item_id: int) -> TransportCatalogRoute | None:
        result = await session.execute(
            select(TransportCatalogRoute).where(TransportCatalogRoute.id == item_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        session: AsyncSession,
        item: TransportCatalogRoute,
        data: TransportCatalogRouteUpdate,
    ) -> TransportCatalogRoute:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        await session.commit()
        await session.refresh(item)
        return item
