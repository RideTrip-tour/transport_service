import asyncio
import logging
from http import HTTPStatus

import httpx

from config import settings


class LocationServiceUnavailableError(Exception):
    pass


logger = logging.getLogger("app.location_client")


class LocationClient:
    def __init__(self) -> None:
        self._base_url = settings.location_service_base_url.rstrip("/")
        self._timeout = settings.location_service_timeout_ms / 1000
        self._retries = max(settings.location_service_retries, 0)

    async def ensure_location_exists(self, location_id: int) -> bool:
        if not self._base_url:
            logger.warning("Location validation skipped because base URL is empty")
            return True

        url = f"{self._base_url}/locations/{location_id}"
        last_error: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.get(url)
                if response.status_code == HTTPStatus.OK:
                    logger.info("Location exists", extra={"location_id": location_id})
                    return True
                if response.status_code == HTTPStatus.NOT_FOUND:
                    logger.warning(
                        "Location not found", extra={"location_id": location_id}
                    )
                    return False
                last_error = RuntimeError(f"Unexpected status: {response.status_code}")
                logger.error(
                    "Unexpected location service status",
                    extra={
                        "location_id": location_id,
                        "status_code": response.status_code,
                    },
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.exception(
                    "Location service call failed",
                    extra={"location_id": location_id, "attempt": attempt + 1},
                )

            if attempt < self._retries:
                await asyncio.sleep(0.2 * (2**attempt))

        logger.error("Location service unavailable", extra={"location_id": location_id})
        raise LocationServiceUnavailableError(str(last_error))
