"""Database-backed webhook job processing."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.detections import evaluate_event
from app.events import normalize_record
from app.models import Event, IngestionJob


async def process_job(db: AsyncSession, job: IngestionJob) -> int:
    """Normalize one claimed job, persist evidence, and evaluate rules."""

    imported = 0
    try:
        # Validate the complete batch before writing anything. A malformed record
        # must fail the job without leaving a partial evidence import behind.
        normalized_records = [normalize_record(record) for record in job.payload]
        for normalized in normalized_records:
            event = Event(organization_id=job.organization_id, **normalized.model_dump())
            db.add(event)
            await db.flush()
            await evaluate_event(db, event)
            imported += 1
        job.status = "completed"
        job.imported_count = imported
        job.completed_at = datetime.now(UTC)
        job.error_code = None
    except ValueError:
        job.status = "failed"
        job.error_code = "invalid_event"
        job.completed_at = datetime.now(UTC)
    await db.commit()
    return imported


async def claim_next_job(db: AsyncSession) -> IngestionJob | None:
    job = await db.scalar(
        select(IngestionJob)
        .where(IngestionJob.status == "queued")
        .order_by(IngestionJob.created_at, IngestionJob.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if job is not None:
        job.status = "processing"
        await db.commit()
    return job
