import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException, UploadFile

from app.api.v1.auth import LoginRequest, current_user, login, logout, me
from app.api.v1.events import (
    event_detail,
    import_events,
    list_events,
    normalize_all,
    overview,
    preview_events,
    read_upload,
)
from app.models import Event, Organization, User
from app.security import hash_password


def make_user() -> User:
    return User(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        email="analyst@example.com",
        display_name="Demo Analyst",
        password_hash=hash_password("avenward-demo-only"),
        role="admin",
    )


def make_event(user: User) -> Event:
    return Event(
        id=uuid.uuid4(),
        organization_id=user.organization_id,
        source="identity",
        category="authentication",
        severity="high",
        title="Synthetic sign-in",
        actor="demo-user",
        target="lab-asset",
        observed_at=datetime(2026, 7, 23, tzinfo=UTC),
        confidence=88,
        summary="Synthetic evidence.",
        raw={"synthetic": True},
    )


def upload(name: str, content: bytes) -> UploadFile:
    item = Mock(spec=UploadFile)
    item.filename = name
    item.read = AsyncMock(return_value=content)
    return item


def database() -> Mock:
    db = Mock()
    db.scalar = AsyncMock()
    db.scalars = AsyncMock()
    db.execute = AsyncMock()
    db.get = AsyncMock()
    db.commit = AsyncMock()
    return db


async def test_current_user_requires_a_valid_session() -> None:
    db = database()
    with pytest.raises(HTTPException) as missing:
        await current_user(db, None)
    assert missing.value.status_code == 401

    db.scalar.return_value = None
    with pytest.raises(HTTPException) as invalid:
        await current_user(db, "Bearer expired")
    assert invalid.value.status_code == 401

    user = make_user()
    db.scalar.return_value = user
    assert await current_user(db, "Bearer valid") is user


async def test_login_me_and_logout_session_lifecycle() -> None:
    user = make_user()
    db = database()
    db.scalar.return_value = user
    result = await login(LoginRequest(email=user.email, password="avenward-demo-only"), db)
    assert result.user["role"] == "admin"
    assert result.token
    db.add.assert_called_once()
    db.commit.assert_awaited_once()

    organization = Organization(id=user.organization_id, name="Avenward Lab")
    db.get.return_value = organization
    identity = await me(user, db)
    assert identity["organization"] == "Avenward Lab"
    db.get.return_value = None
    assert (await me(user, db))["organization"] == "Unknown"

    db.reset_mock()
    await logout(user, db, "Bearer valid")
    db.execute.assert_awaited_once()
    db.commit.assert_awaited_once()


async def test_login_rejects_unknown_or_wrong_credentials() -> None:
    db = database()
    db.scalar.return_value = None
    with pytest.raises(HTTPException) as unknown:
        await login(LoginRequest(email="unknown@example.com", password="long-password"), db)
    assert unknown.value.status_code == 401

    db.scalar.return_value = make_user()
    with pytest.raises(HTTPException) as wrong:
        await login(LoginRequest(email="analyst@example.com", password="wrong-password"), db)
    assert wrong.value.status_code == 401


async def test_upload_limits_and_preview_validation() -> None:
    user = make_user()
    valid = upload(
        "events.json",
        b'{"title":"Synthetic","severity":"low","observed_at":"2026-07-23T10:00:00Z"}',
    )
    result = await preview_events(valid, user)
    assert result["count"] == 1

    with pytest.raises(HTTPException) as invalid:
        await read_upload(upload("events.exe", b"not executable"))
    assert invalid.value.status_code == 422

    with pytest.raises(HTTPException) as large:
        await read_upload(upload("events.json", b"x" * 2_000_001))
    assert large.value.status_code == 413

    with pytest.raises(HTTPException, match="no events"):
        normalize_all([])
    with pytest.raises(HTTPException, match="too many"):
        normalize_all([{}] * 5001)
    with pytest.raises(HTTPException):
        normalize_all([{"severity": "dramatic"}])


async def test_import_search_overview_and_detail_are_tenant_scoped() -> None:
    user = make_user()
    item = make_event(user)
    db = database()
    valid = upload(
        "events.jsonl",
        b'{"title":"Synthetic","severity":"high","observed_at":"2026-07-23T10:00:00Z"}',
    )
    imported = await import_events(valid, user, db)
    assert imported == {"imported": 1}
    db.add_all.assert_called_once()
    db.commit.assert_awaited_once()

    db.scalar.return_value = 1
    db.scalars.return_value = [item]
    page = await list_events(user, db, "sign-in", "high", 1, 25)
    assert page.total == 1
    assert page.items[0].title == "Synthetic sign-in"
    count_query = str(db.scalar.await_args.args[0])
    assert "events.organization_id" in count_query

    db.execute.return_value = [("high", 1), ("low", 2)]
    summary = await overview(user, db)
    assert summary == {"total": 3, "by_severity": {"high": 1, "low": 2}}

    db.scalar.return_value = item
    assert await event_detail(item.id, user, db) is item
    db.scalar.return_value = None
    with pytest.raises(HTTPException) as missing:
        await event_detail(uuid.uuid4(), user, db)
    assert missing.value.status_code == 404
