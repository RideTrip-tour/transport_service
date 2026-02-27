from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends

from app.db.database import get_async_session

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    """Проверка liveliness: сервис запущен и отвечает на HTTP-запросы."""
    return {"status": "ok"}


@router.get("/ready")
async def ready(session: AsyncSession = Depends(get_async_session)) -> dict[str, str]:
    """Проверка readiness: сервис готов обрабатывать трафик и имеет доступ к БД."""
    await session.execute(text("SELECT 1"))
    return {"status": "ok"}
