"""Idempotent local-only demo identity and synthetic event seeding."""

import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.core.config import get_settings
from app.db import SessionFactory, engine
from app.models import (
    AuditRecord,
    DetectionRule,
    Event,
    IngestionSource,
    Investigation,
    InvestigationComment,
    InvestigationLink,
    Organization,
    User,
    VulnerabilityFinding,
)
from app.security import hash_password, token_digest


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
            user = User(
                organization_id=organization.id,
                email=settings.demo_email.lower(),
                display_name="Demo Analyst",
                password_hash=hash_password(settings.demo_password),
                role="admin",
            )
            db.add(user)
            await db.flush()
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
        source = await db.scalar(
            select(IngestionSource).where(
                IngestionSource.organization_id == organization.id,
                IngestionSource.name == "Local webhook",
            )
        )
        if source is None:
            db.add(
                IngestionSource(
                    organization_id=organization.id,
                    name="Local webhook",
                    token_hash=token_digest(settings.demo_ingest_key),
                    enabled=True,
                )
            )
        rule_count = await db.scalar(
            select(func.count())
            .select_from(DetectionRule)
            .where(DetectionRule.organization_id == organization.id)
        )
        if not rule_count:
            db.add_all(
                [
                    DetectionRule(
                        organization_id=organization.id,
                        slug="repeated-authentication-failure",
                        name="Repeated authentication failures",
                        description=(
                            "Three authentication failure events for one actor within 15 minutes."
                        ),
                        version=1,
                        enabled=True,
                        severity="high",
                        conditions=[
                            {"field": "category", "operator": "equals", "value": "authentication"},
                            {"field": "title", "operator": "contains", "value": "failure"},
                        ],
                        group_by="actor",
                        threshold=3,
                        window_seconds=900,
                    ),
                    DetectionRule(
                        organization_id=organization.id,
                        slug="service-offline",
                        name="Service or asset reported offline",
                        description="An availability event reports an offline service or asset.",
                        version=1,
                        enabled=True,
                        severity="high",
                        conditions=[
                            {"field": "category", "operator": "equals", "value": "availability"},
                            {"field": "title", "operator": "contains", "value": "offline"},
                        ],
                        group_by="target",
                        threshold=1,
                        window_seconds=300,
                    ),
                ]
            )
        finding = await db.scalar(
            select(VulnerabilityFinding).where(
                VulnerabilityFinding.organization_id == organization.id,
                VulnerabilityFinding.source == "synthetic-scanner",
                VulnerabilityFinding.external_id == "AVEN-DEMO-001",
            )
        )
        if finding is None:
            now = datetime.now(UTC).replace(microsecond=0)
            finding = VulnerabilityFinding(
                organization_id=organization.id,
                source="synthetic-scanner",
                external_id="AVEN-DEMO-001",
                asset_identifier="lab-web-01",
                title="Outdated demonstration web component",
                severity="high",
                cvss_score_tenths=81,
                cve=None,
                description=(
                    "Synthetic scanner output indicating an outdated component in the lab."
                ),
                remediation=(
                    "Verify the installed version, test the supported update, and deploy it "
                    "through the organization's approved change process."
                ),
                evidence={"synthetic": True, "scanner_plugin": "demo-001"},
                status="open",
                exception_reason=None,
                first_seen_at=now - timedelta(days=2),
                last_seen_at=now,
            )
            db.add(finding)
            await db.flush()
        else:
            # Keep the bundled public-demo record unmistakably synthetic. It must
            # never resemble an assigned CVE or imply a real vulnerable product.
            finding.cve = None
        investigation = await db.scalar(
            select(Investigation).where(
                Investigation.organization_id == organization.id,
                Investigation.title == "Review lab web exposure",
            )
        )
        if investigation is None:
            investigation = Investigation(
                organization_id=organization.id,
                title="Review lab web exposure",
                summary=(
                    "Confirm the synthetic vulnerability finding, determine ownership, and "
                    "document the approved remediation path."
                ),
                severity="high",
                status="open",
                owner_id=user.id,
                resolution=None,
                created_by_id=user.id,
            )
            db.add(investigation)
            await db.flush()
            db.add_all(
                [
                    InvestigationLink(
                        organization_id=organization.id,
                        investigation_id=investigation.id,
                        entity_type="finding",
                        entity_id=finding.id,
                        created_by_id=user.id,
                    ),
                    InvestigationComment(
                        organization_id=organization.id,
                        investigation_id=investigation.id,
                        author_id=user.id,
                        body="Synthetic case created for the Phase 3 investigation workflow.",
                    ),
                    AuditRecord(
                        organization_id=organization.id,
                        actor_id=user.id,
                        entity_type="investigation",
                        entity_id=investigation.id,
                        action="investigation.created",
                        details={"synthetic": True},
                    ),
                ]
            )
        elif investigation.status == "resolved":
            # The synthetic case and its synthetic finding describe one completed
            # demo workflow, so their public-facing states should remain aligned.
            finding.status = "resolved"
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
