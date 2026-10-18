"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, Depends, FastAPI

from taskboard import __version__
from taskboard.api.deps import require_service_auth
from taskboard.api.errors import register_error_handlers
from taskboard.api.middleware import BodySizeLimitMiddleware, RequestContextMiddleware
from taskboard.api.routers import admin, auth, health, projects, tasks, teams
from taskboard.composition import Infrastructure, build_infrastructure
from taskboard.config import Settings, get_settings
from taskboard.logging_setup import configure_logging

API_PREFIX = "/api/v1"
# Multipart framing around a maximum-size file.
_MULTIPART_OVERHEAD = 64 * 1024


def create_app(settings: Settings | None = None, infra: Infrastructure | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    infrastructure = infra or build_infrastructure(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        infrastructure.close()

    app = FastAPI(
        title="Taskboard API",
        version=__version__,
        # The OpenAPI document is served below, behind service authentication; no docs UI.
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.infra = infrastructure

    v1 = APIRouter(prefix=API_PREFIX, dependencies=[Depends(require_service_auth)])
    for module in (auth, teams, projects, tasks, admin):
        v1.include_router(module.router)

    @v1.get("/openapi.json", include_in_schema=False)
    def openapi_document() -> dict[str, Any]:
        return app.openapi()

    app.include_router(v1)
    app.include_router(health.router)

    register_error_handlers(app)
    app.add_middleware(
        BodySizeLimitMiddleware, max_bytes=settings.max_upload_bytes + _MULTIPART_OVERHEAD
    )
    app.add_middleware(RequestContextMiddleware)
    return app
