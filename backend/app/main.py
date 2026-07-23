"""Avenward ASGI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import request_id_middleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Configure process resources without connecting eagerly to dependencies."""

    configure_logging(get_settings().log_level)
    yield


def create_app() -> FastAPI:
    """Construct the API for production and isolated tests."""

    settings = get_settings()
    application = FastAPI(
        title="Avenward API",
        description="Defensive security and operations platform API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    application.middleware("http")(request_id_middleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
    application.include_router(api_router, prefix="/api/v1")
    return application


app = create_app()
