"""Idempotent local-only demo identity and synthetic event seeding."""

import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.core.config import get_settings
from app.db import SessionFactory, engine
from app.models import Event, Organization, User
from app.security import hash_password


async def seed() -> None:
    settings = get_settings()
    if settings.environment != "development":
        return
    async with SessionFactory() as db:
        organization = await db.scalar(
            select(Organization).where(Organization.name == "Avenward Lab")
        )
        if organization is None:
            organization = Organization(name="Avenward Lab")
            db.add(organization)
            await db.flush()
        user = await db.scalar(select(User).where(User.email == settings.demo_email.lower()))
        if user is None:
            db.add(
                User(
                    organization_id=organization.id,
                    email=settings.demo_email.lower(),
                    display_name="Demo Analyst",
                    password_hash=hash_password(settings.demo_password),
                    role="admin",
                )
            )
        count = await db.scalar(
            select(func.count()).select_from(Event).where(Event.organization_id == organization.id)
        )
        if not count:
            severities = ["informational", "low", "medium", "high"]
            titles = [
                "Successful interactive sign-in",
                "New administrative group membership",
                "Endpoint malware scan completed",
                "Repeated authentication failure",
                "Network device configuration changed",
                "Unusual outbound connection observed",
            ]
            now = datetime.now(UTC).replace(microsecond=0)
            for index in range(36):
                severity = severities[(index * 7) % len(severities)]
                title = titles[index % len(titles)]
                raw = {"synthetic": True, "sequence": index + 1, "generator": "avenward-0.1.0"}
                db.add(
                    Event(
                        organization_id=organization.id,
                        source=["identity", "endpoint", "network"][index % 3],
                        category=["authentication", "configuration", "connection"][index % 3],
                        severity=severity,
                        title=title,
                        actor=f"demo-user-{index % 7}",
                        target=f"lab-asset-{index % 9}",
                        observed_at=now - timedelta(minutes=index * 37),
                        confidence=70 + ((index * 11) % 29),
                        summary=(
                            "Deterministic synthetic evidence for the authorized "
                            "Avenward demonstration environment."
                        ),
                        raw=raw,
                    )
                )
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
