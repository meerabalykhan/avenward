from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1 import health as health_module
from app.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client


async def test_health_is_live_and_returns_request_id(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health", headers={"X-Request-ID": "test-request"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"] == "test-request"


async def test_invalid_request_id_is_replaced(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health", headers={"X-Request-ID": "unsafe value"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "unsafe value"


async def test_version_returns_public_metadata(client: AsyncClient) -> None:
    response = await client.get("/api/v1/version")

    assert response.status_code == 200
    assert response.json() == {
        "name": "avenward",
        "version": "0.2.0",
        "environment": "development",
    }


async def test_readiness_fails_closed_when_dependencies_are_unavailable(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def unavailable(*_: object, **__: object) -> str:
        return "unavailable"

    monkeypatch.setattr(health_module, "run_probe", unavailable)
    response = await client.get("/api/v1/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {"postgres": "unavailable", "redis": "unavailable"},
    }


async def test_readiness_succeeds_when_dependencies_are_available(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def available(*_: object, **__: object) -> str:
        return "available"

    monkeypatch.setattr(health_module, "run_probe", available)
    response = await client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"postgres": "available", "redis": "available"},
    }
