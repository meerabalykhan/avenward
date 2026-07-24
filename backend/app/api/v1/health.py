"""Liveness, readiness, and build metadata endpoints."""

from functools import partial

from fastapi import APIRouter, Response, status

from app.core.config import Settings, get_settings
from app.core.dependencies import check_postgres, check_redis, run_probe
from app.schemas import HealthResponse, ReadinessResponse, VersionResponse

router = APIRouter(tags=["system"])
APP_VERSION = "0.3.0"


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return process liveness without checking external dependencies."""

    return HealthResponse()


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessResponse}},
)
async def readiness(response: Response) -> ReadinessResponse:
    """Return dependency readiness while withholding sensitive error details."""

    settings = get_settings()
    checks = {
        "postgres": await run_probe(
            partial(check_postgres, settings), settings.readiness_timeout_seconds
        ),
        "redis": await run_probe(
            partial(check_redis, settings), settings.readiness_timeout_seconds
        ),
    }
    is_ready = all(value == "available" for value in checks.values())
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(status="ready" if is_ready else "not_ready", checks=checks)


@router.get("/version", response_model=VersionResponse)
async def version() -> VersionResponse:
    """Return non-sensitive application build metadata."""

    settings: Settings = get_settings()
    return VersionResponse(version=APP_VERSION, environment=settings.environment)
