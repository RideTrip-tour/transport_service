from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TransportRequest
from app.schemas.transport_request import TransportRequestCreate, TransportRequestUpdate


class TransportRequestCrud:
    @staticmethod
    async def create(
        session: AsyncSession,
        data: TransportRequestCreate,
        commit: bool = True,
    ) -> TransportRequest:
        item = TransportRequest(
            **data.model_dump(),
            type=data.type.value,
        )
        session.add(item)
        await session.flush()
        if commit:
            await session.commit()
        await session.refresh(item)
        return item

    @staticmethod
    async def get(session: AsyncSession, item_id: int) -> TransportRequest | None:
        result = await session.execute(
            select(TransportRequest).where(TransportRequest.id == item_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_user(
        session: AsyncSession, user_id: int
    ) -> list[TransportRequest]:
        result = await session.execute(
            select(TransportRequest).where(TransportRequest.user_id == user_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update(
        session: AsyncSession,
        item: TransportRequest,
        data: TransportRequestUpdate,
        commit: bool = True,
    ) -> TransportRequest:
        payload = data.model_dump(exclude_unset=True)
        if "type" in payload and payload["type"] is not None:
            payload["type"] = payload["type"].value
        if "status" in payload and payload["status"] is not None:
            payload["status"] = payload["status"].value

        for field, value in payload.items():
            setattr(item, field, value)

        await session.flush()
        if commit:
            await session.commit()
        await session.refresh(item)
        return item
