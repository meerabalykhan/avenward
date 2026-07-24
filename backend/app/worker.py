"""Small database-backed worker for bounded ingestion jobs."""

import asyncio
import logging

from app.core.config import get_settings
from app.db import SessionFactory
from app.ingestion import claim_next_job, process_job

logger = logging.getLogger(__name__)


async def run() -> None:
    settings = get_settings()
    while True:
        async with SessionFactory() as db:
            job = await claim_next_job(db)
            if job is not None:
                await process_job(db, job)
                logger.info("ingestion_job_finished", extra={"job_id": str(job.id)})
        if job is None:
            await asyncio.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    asyncio.run(run())
