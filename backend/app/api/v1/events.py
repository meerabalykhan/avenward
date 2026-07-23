"""Tenant-scoped event preview, import, search, detail, and overview APIs."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import func, or_, select

from app.api.v1.auth import CurrentUser, DatabaseSession
from app.core.config import get_settings
from app.events import NormalizedEvent, normalize_record, records_from_upload
from app.models import Event

router = APIRouter(prefix="/events", tags=["events"])

EventUpload = Annotated[UploadFile, File()]


class EventView(BaseModel):
    id: uuid.UUID
    source: str
    category: str
    severity: str
    title: str
    actor: str | None
    target: str | None
    observed_at: datetime
    confidence: int
    summary: str

    model_config = {"from_attributes": True}


class EventPage(BaseModel):
    items: list[EventView]
    page: int
    page_size: int
    total: int


async def read_upload(upload: UploadFile) -> list[dict[str, object]]:
    data = await upload.read(get_settings().upload_max_bytes + 1)
    if len(data) > get_settings().upload_max_bytes:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "Upload is too large")
    try:
        return records_from_upload(upload.filename or "", data)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc


def normalize_all(records: list[dict[str, object]]) -> list[NormalizedEvent]:
    if not records:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "File contains no events")
    if len(records) > 5000:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "File contains too many events")
    try:
        return [normalize_record(record) for record in records]
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc


@router.post("/preview")
async def preview_events(upload: EventUpload, user: CurrentUser) -> dict[str, object]:
    del user
    events = normalize_all(await read_upload(upload))
    return {"count": len(events), "sample": [event.model_dump(mode="json") for event in events[:5]]}


@router.post("/import", status_code=status.HTTP_201_CREATED)
async def import_events(
    upload: EventUpload,
    user: CurrentUser,
    db: DatabaseSession,
) -> dict[str, int]:
    events = normalize_all(await read_upload(upload))
    db.add_all(
        [Event(organization_id=user.organization_id, **event.model_dump()) for event in events]
    )
    await db.commit()
    return {"imported": len(events)}


@router.get("", response_model=EventPage)
async def list_events(
    user: CurrentUser,
    db: DatabaseSession,
    q: Annotated[str | None, Query(max_length=120)] = None,
    severity: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> EventPage:
    filters = [Event.organization_id == user.organization_id]
    if severity:
        filters.append(Event.severity == severity.lower())
    if q:
        pattern = f"%{q}%"
        filters.append(
            or_(Event.title.ilike(pattern), Event.actor.ilike(pattern), Event.target.ilike(pattern))
        )
    total = await db.scalar(select(func.count()).select_from(Event).where(*filters)) or 0
    rows = await db.scalars(
        select(Event)
        .where(*filters)
        .order_by(Event.observed_at.desc(), Event.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return EventPage(items=list(rows), page=page, page_size=page_size, total=total)


@router.get("/overview")
async def overview(user: CurrentUser, db: DatabaseSession) -> dict[str, object]:
    rows = await db.execute(
        select(Event.severity, func.count())
        .where(Event.organization_id == user.organization_id)
        .group_by(Event.severity)
    )
    counts = {severity: count for severity, count in rows}
    return {"total": sum(counts.values()), "by_severity": counts}


@router.get("/{event_id}", response_model=EventView)
async def event_detail(
    event_id: uuid.UUID,
    user: CurrentUser,
    db: DatabaseSession,
) -> Event:
    event = await db.scalar(
        select(Event).where(Event.id == event_id, Event.organization_id == user.organization_id)
    )
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found")
    return event
