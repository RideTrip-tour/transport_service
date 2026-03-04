from contextlib import asynccontextmanager
import logging
import logging.config
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routes import health_router, routes_router
from app.errors import AppError, PayloadTooLargeAppError
from app.services.observability import observability_registry
from app.schemas.api_error import ApiErrorResponse
from config import settings
from app.utils.logging import LOGGING_CONFIG
from app.utils.request_context import (
    RequestContext,
    clear_request_context,
    set_request_context,
)

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Log startup/shutdown lifecycle events."""
    yield


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/api/transport/docs",
        redoc_url="/api/transport/redoc",
        openapi_url="/api/transport/openapi.json",
    )

    api_prefix = "/api/transport"
    app.include_router(routes_router, prefix=api_prefix)
    app.include_router(health_router, prefix=api_prefix)

    @app.middleware("http")
    async def correlation_middleware(request: Request, call_next):
        """Attach request/trace ids and enforce body size guardrail."""
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        trace_id = request.headers.get("X-Trace-ID") or str(uuid4())
        request.state.request_id = request_id
        request.state.trace_id = trace_id

        content_length = request.headers.get("Content-Length")
        content_length_int = int(content_length) if content_length and content_length.isdigit() else None
        if content_length_int and content_length_int > settings.max_request_body_bytes:
            exc = PayloadTooLargeAppError(
                message="Request payload is too large",
                details={
                    "content_length": content_length_int,
                    "max_request_body_bytes": settings.max_request_body_bytes,
                },
            )
            observability_registry.record_error_code(exc.code)
            return JSONResponse(
                status_code=exc.status_code,
                content=ApiErrorResponse(
                    code=exc.code,
                    message=exc.message,
                    details=exc.details,
                    trace_id=trace_id,
                ).model_dump(),
                headers={"X-Request-ID": request_id, "X-Trace-ID": trace_id},
            )

        set_request_context(RequestContext(request_id=request_id, trace_id=trace_id))
        response = await call_next(request)
        clear_request_context()

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Render unified API error payload with correlation identifiers."""
        trace_id = getattr(request.state, "trace_id", str(uuid4()))
        request_id = getattr(request.state, "request_id", str(uuid4()))
        observability_registry.record_error_code(exc.code)
        logger.warning(
            "AppError handled",
            extra={
                "error_code": exc.code,
                "status_code": exc.status_code,
                "details": exc.details,
            },
        )
        error = ApiErrorResponse(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            trace_id=trace_id,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error.model_dump(),
            headers={"X-Request-ID": request_id, "X-Trace-ID": trace_id},
        )

    return app


app = create_app()
