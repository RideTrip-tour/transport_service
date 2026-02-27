from app.routes.health import router as health_router
from app.routes.route_planner import router as planner_router
from app.routes.transport_catalog import router as transport_catalog_router
from app.routes.transport_requests import router as transport_requests_router
from app.routes.transport_types import router as transport_types_router

__all__ = [
    "health_router",
    "planner_router",
    "transport_catalog_router",
    "transport_requests_router",
    "transport_types_router",
]
