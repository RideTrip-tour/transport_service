from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TransportQuote


class TransportQuoteCrud:
    @staticmethod
    async def create(session: AsyncSession, **kwargs) -> TransportQuote:
        item = TransportQuote(**kwargs)
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item
