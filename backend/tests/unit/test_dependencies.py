import asyncio
from typing import Any

import pytest

from app.core import dependencies
from app.core.config import Settings
from app.core.dependencies import check_postgres, check_redis, run_probe


async def test_run_probe_reports_available() -> None:
    async def succeeds() -> None:
        return None

    assert await run_probe(succeeds, timeout_seconds=0.1) == "available"


async def test_run_probe_collapses_errors() -> None:
    async def fails() -> None:
        raise RuntimeError("sensitive detail")

    assert await run_probe(fails, timeout_seconds=0.1) == "unavailable"


async def test_run_probe_times_out() -> None:
    async def waits() -> None:
        await asyncio.sleep(0.1)

    assert await run_probe(waits, timeout_seconds=0.001) == "unavailable"


async def test_postgres_probe_executes_read_only_ping(monkeypatch: pytest.MonkeyPatch) -> None:
    executed: list[str] = []
    disposed = False

    class FakeConnection:
        async def __aenter__(self) -> "FakeConnection":
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def execute(self, statement: object) -> None:
            executed.append(str(statement))

    class FakeEngine:
        def connect(self) -> FakeConnection:
            return FakeConnection()

        async def dispose(self) -> None:
            nonlocal disposed
            disposed = True

    monkeypatch.setattr(dependencies, "create_async_engine", lambda *_args, **_kwargs: FakeEngine())

    await check_postgres(Settings())

    assert executed == ["SELECT 1"]
    assert disposed is True


async def test_redis_probe_pings_and_closes(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    class FakeClient:
        async def ping(self) -> bool:
            calls.append("ping")
            return True

        async def aclose(self) -> None:
            calls.append("close")

    class FakeRedis:
        @staticmethod
        def from_url(*_args: object, **_kwargs: object) -> Any:
            return FakeClient()

    monkeypatch.setattr(dependencies, "Redis", FakeRedis)

    await check_redis(Settings())

    assert calls == ["ping", "close"]
