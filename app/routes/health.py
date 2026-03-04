import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.db.database import get_async_session
from app.services.cache.segment_cache_repository import SegmentCacheRepository
from app.services.observability import observability_registry

logger = logging.getLogger("app.health")

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    """Проверка liveliness: сервис запущен и отвечает на HTTP-запросы."""
    return {"status": "ok"}


@router.get("/ready")
async def ready(session: AsyncSession = Depends(get_async_session)) -> JSONResponse:
    """Проверка readiness: сервис готов обрабатывать трафик и имеет доступ к критичным зависимостям."""
    checks = {
        "database": "ok",
        "redis": "ok",
    }
    try:
        await session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        checks["database"] = "error"
        logger.exception("Database readiness check failed")

    cache_repo = SegmentCacheRepository()
    client = getattr(cache_repo, "_client", None)
    if client is not None and hasattr(client, "ping"):
        try:
            await asyncio.wait_for(client.ping(), timeout=0.2)
        except Exception:  # noqa: BLE001
            checks["redis"] = "error"
            logger.exception("Redis readiness check failed")
    elif client is None:
        checks["redis"] = "disabled"

    status = "ok" if checks["database"] == "ok" else "error"
    status_code = 200 if status == "ok" else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": status,
            "checks": checks,
        },
    )


@router.get("/metrics")
async def metrics() -> dict:
    """Return operational metrics snapshot for dashboards and alerts."""
    return observability_registry.snapshot()
