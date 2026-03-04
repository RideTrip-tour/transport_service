from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SearchHistory


class SearchHistoryCrud:
    @staticmethod
    async def create(
        session: AsyncSession,
        data: dict,
        commit: bool = True,
    ) -> SearchHistory:
        item = SearchHistory(**data)
        session.add(item)
        await session.flush()
        if commit:
            await session.commit()
        await session.refresh(item)
        return item

    @staticmethod
    async def list_recent_by_user(
        session: AsyncSession,
        user_id: int,
        limit: int = 20,
    ) -> list[SearchHistory]:
        result = await session.execute(
            select(SearchHistory)
            .where(SearchHistory.user_id == user_id)
            .order_by(SearchHistory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

