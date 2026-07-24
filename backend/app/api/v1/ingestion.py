"""Authenticated, bounded webhook ingestion that queues inert event data."""

import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from app.api.v1.auth import DatabaseSession
from app.core.config import get_settings
from app.models import IngestionJob, IngestionSource
from app.security import token_digest

router = APIRouter(prefix="/ingestion", tags=["ingestion"])
IngestKey = Annotated[str | None, Header(alias="X-Avenward-Ingest-Key")]


class WebhookBatch(BaseModel):
    events: list[dict[str, Any]] = Field(min_length=1)

    @field_validator("events")
    @classmethod
    def bounded_batch(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(value) > get_settings().webhook_max_events:
            raise ValueError("webhook batch contains too many events")
        return value


class JobAccepted(BaseModel):
    job_id: uuid.UUID
    status: str
    received: int


@router.post("/webhook", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_webhook(
    payload: WebhookBatch,
    db: DatabaseSession,
    ingest_key: IngestKey = None,
) -> JobAccepted:
    if not ingest_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Ingestion key required")
    source = await db.scalar(
        select(IngestionSource).where(
            IngestionSource.token_hash == token_digest(ingest_key),
            IngestionSource.enabled.is_(True),
        )
    )
    if source is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Ingestion key is invalid")
    source.last_seen_at = datetime.now(UTC)
    job = IngestionJob(
        organization_id=source.organization_id,
        source_id=source.id,
        status="queued",
        payload=payload.events,
        received_count=len(payload.events),
        imported_count=0,
    )
    db.add(job)
    await db.commit()
    return JobAccepted(job_id=job.id, status=job.status, received=job.received_count)
