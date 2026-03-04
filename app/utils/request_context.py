"""Request-scoped correlation context helpers."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class RequestContext:
    """Correlation identifiers bound to current request lifecycle."""

    request_id: str
    trace_id: str


_REQUEST_CONTEXT: ContextVar[RequestContext | None] = ContextVar(
    "request_context",
    default=None,
)


def set_request_context(context: RequestContext) -> None:
    """Bind request context to current async execution context."""
    _REQUEST_CONTEXT.set(context)


def clear_request_context() -> None:
    """Clear request context after request completion."""
    _REQUEST_CONTEXT.set(None)


def get_request_context() -> RequestContext | None:
    """Return current request context or None when missing."""
    return _REQUEST_CONTEXT.get()
