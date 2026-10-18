"""Liveness and readiness probes. Unauthenticated, outside /api/v1."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from taskboard.api.deps import get_infra
from taskboard.composition import Infrastructure

router = APIRouter(tags=["health"])
logger = logging.getLogger("taskboard.health")


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
def readyz(infra: Annotated[Infrastructure, Depends(get_infra)]) -> JSONResponse:
    """Ready when PostgreSQL and storage work. Redis is reported but optional (degraded mode)."""
    checks: dict[str, str] = {}
    ready = True
    try:
        infra.check_database()
        checks["database"] = "ok"
    except Exception:
        logger.warning("readiness: database unavailable")
        checks["database"] = "unavailable"
        ready = False
    try:
        infra.storage.check()
        checks["storage"] = "ok"
    except Exception:
        logger.warning("readiness: storage unavailable")
        checks["storage"] = "unavailable"
        ready = False
    if infra.settings.redis_url is None:
        checks["redis"] = "disabled"
    else:
        checks["redis"] = "ok" if infra.check_redis() else "degraded"
    return JSONResponse(
        {"status": "ready" if ready else "not_ready", "checks": checks},
        status_code=200 if ready else 503,
    )
