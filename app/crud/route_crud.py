from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Route


class RouteCrud:
    @staticmethod
    async def create(
        session: AsyncSession,
        data: dict,
        commit: bool = True,
    ) -> Route:
        item = Route(**data)
        session.add(item)
        await session.flush()
        if commit:
            await session.commit()
        await session.refresh(item)
        return item

    @staticmethod
    async def get(session: AsyncSession, route_id: int) -> Route | None:
        result = await session.execute(select(Route).where(Route.id == route_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_ids(session: AsyncSession, route_ids: list[int]) -> list[Route]:
        if not route_ids:
            return []
        result = await session.execute(select(Route).where(Route.id.in_(route_ids)))
        return list(result.scalars().all())

    @staticmethod
    async def update_with_new_version(
        session: AsyncSession,
        item: Route,
        data: dict,
        commit: bool = True,
    ) -> Route:
        for field, value in data.items():
            setattr(item, field, value)
        item.route_version += 1
        item.recalculated_at = datetime.now(timezone.utc)
        await session.flush()
        if commit:
            await session.commit()
        await session.refresh(item)
        return item

