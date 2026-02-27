# src/main.py
from contextlib import asynccontextmanager
import logging
import logging.config

from fastapi import FastAPI

from app.routes import (
    health_router,
    planner_router,
    transport_catalog_router,
    transport_requests_router,
    transport_types_router,
)
from config import settings
from app.utils.logging import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Service is starting up...")
    
    yield
    
    logging.info("Service is shutting down...")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/api/transport/docs",
        redoc_url="/api/transport/redoc",
        openapi_url="/api/transport/openapi.json",
    )

    api_prefix = "/api/transport"
    app.include_router(transport_types_router, prefix=api_prefix)
    app.include_router(transport_catalog_router, prefix=api_prefix)
    app.include_router(transport_requests_router, prefix=api_prefix)
    app.include_router(planner_router, prefix=api_prefix)
    app.include_router(health_router, prefix=api_prefix)

    return app

app = create_app()
