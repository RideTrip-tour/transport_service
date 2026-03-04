import logging
import logging.config

from app.utils.request_context import get_request_context


class RequestContextFilter(logging.Filter):
    """Inject request/trace identifiers from contextvars into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Populate correlation ids for every log entry."""
        context = get_request_context()
        record.request_id = context.request_id if context else "-"
        record.trace_id = context.trace_id if context else "-"
        return True


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_context": {
            "()": RequestContextFilter,
        },
    },
    "formatters": {
        "default": {
            "format": (
                "%(asctime)s [%(levelname)s] %(name)s request_id=%(request_id)s "
                "trace_id=%(trace_id)s: %(message)s"
            ),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "filters": ["request_context"],
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "app": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "users": {  # твой логгер
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn": {  # включаем логи uvicorn
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "level": "ERROR",
        },
        "uvicorn.access": {  # access logs
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
