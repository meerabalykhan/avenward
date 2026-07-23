"""Bounded infrastructure readiness probes."""

import asyncio
from collections.abc import Awaitable, Callable

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings

Probe = Callable[[], Awaitable[None]]


async def check_postgres(settings: Settings) -> None:
    """Run a bounded, read-only PostgreSQL connectivity probe."""

    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    finally:
        await engine.dispose()


async def check_redis(settings: Settings) -> None:
    """Run a bounded Redis connectivity probe."""

    client: Redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await client.ping()
    finally:
        await client.aclose()


async def run_probe(probe: Probe, timeout_seconds: float) -> str:
    """Return a stable status without exposing connection details or errors."""

    try:
        async with asyncio.timeout(timeout_seconds):
            await probe()
    except (TimeoutError, OSError, RuntimeError, ValueError):
        return "unavailable"
    except Exception:  # noqa: BLE001 - readiness must safely collapse driver errors
        return "unavailable"
    return "available"
