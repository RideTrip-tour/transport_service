from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TransportType
from app.schemas.transport_type import TransportTypeCreate, TransportTypeUpdate


class TransportTypeCrud:
    @staticmethod
    async def create(session: AsyncSession, data: TransportTypeCreate) -> TransportType:
        item = TransportType(**data.model_dump())
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item

    @staticmethod
    async def list(session: AsyncSession) -> list[TransportType]:
        result = await session.execute(select(TransportType))
        return list(result.scalars().all())

    @staticmethod
    async def get(session: AsyncSession, item_id: int) -> TransportType | None:
        result = await session.execute(
            select(TransportType).where(TransportType.id == item_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_code(session: AsyncSession, code: str) -> TransportType | None:
        result = await session.execute(
            select(TransportType).where(TransportType.code == code)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        session: AsyncSession,
        item: TransportType,
        data: TransportTypeUpdate,
    ) -> TransportType:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        await session.commit()
        await session.refresh(item)
        return item
