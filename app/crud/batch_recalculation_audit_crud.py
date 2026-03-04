"""CRUD helpers for batch recalculation audit model."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BatchRecalculationAudit


class BatchRecalculationAuditCrud:
    """CRUD operations for batch recalculation audit records."""

    @staticmethod
    async def create(
        session: AsyncSession,
        data: dict,
        commit: bool = True,
    ) -> BatchRecalculationAudit:
        """Create audit record and optionally commit transaction."""
        item = BatchRecalculationAudit(**data)
        session.add(item)
        await session.flush()
        if commit:
            await session.commit()
        await session.refresh(item)
        return item

