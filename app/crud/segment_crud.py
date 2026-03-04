from datetime import date, datetime, time, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Segment


class SegmentCrud:
    @staticmethod
    async def create_many(
        session: AsyncSession,
        items: list[dict],
        commit: bool = True,
    ) -> list[Segment]:
        """Create or reuse segments by unique pair (provider, external_id)."""
        segments: list[Segment] = []
        for item in items:
            existing = await session.scalar(
                select(Segment)
                .where(Segment.provider == item["provider"])
                .where(Segment.external_id == item["external_id"])
            )
            if existing is not None:
                segments.append(existing)
                continue

            created = Segment(**item)
            session.add(created)
            await session.flush()
            await session.refresh(created)
            segments.append(created)
        if commit:
            await session.commit()
        return segments

    @staticmethod
    async def list_by_direction_date(
        session: AsyncSession,
        origin_hub_id: int,
        destination_hub_id: int,
        departure_date: date,
    ) -> list[Segment]:
        start = datetime.combine(departure_date, time.min, tzinfo=timezone.utc)
        end = datetime.combine(departure_date, time.max, tzinfo=timezone.utc)
        result = await session.execute(
            select(Segment)
            .where(Segment.origin_hub_id == origin_hub_id)
            .where(Segment.destination_hub_id == destination_hub_id)
            .where(Segment.departure_time >= start)
            .where(Segment.departure_time <= end)
            .order_by(Segment.departure_time.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete_expired(session: AsyncSession, commit: bool = True) -> int:
        stmt = delete(Segment).where(
                Segment.expires_at.is_not(None),
                Segment.expires_at < datetime.now(timezone.utc),
            )
        result = await session.execute(
            stmt.execution_options(synchronize_session=False)
        )
        if commit:
            await session.commit()
        return int(result.rowcount or 0)
