import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.v1.alerts import (
    AlertStateChange,
    alert_detail,
    change_alert_status,
    list_alerts,
    list_rules,
)
from app.api.v1.ingestion import WebhookBatch, enqueue_webhook
from app.detections import (
    RuleCondition,
    RuleDefinition,
    alert_dedup_key,
    evaluate_event,
    event_group,
    event_matches,
)
from app.ingestion import claim_next_job, process_job
from app.models import Alert, DetectionRule, Event, IngestionJob, IngestionSource, User
from app.security import token_digest


def database() -> Mock:
    db = Mock()
    db.scalar = AsyncMock()
    db.scalars = AsyncMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    return db


def user() -> User:
    return User(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        email="analyst@example.com",
        display_name="Analyst",
        password_hash="unused",
        role="admin",
    )


def event(owner: User, *, title: str = "Authentication failure") -> Event:
    return Event(
        id=uuid.uuid4(),
        organization_id=owner.organization_id,
        source="identity",
        category="authentication",
        severity="high",
        title=title,
        actor="alice",
        target="portal",
        observed_at=datetime(2026, 7, 24, 10, 0, tzinfo=UTC),
        confidence=90,
        summary="Synthetic evidence.",
        raw={"synthetic": True},
    )


def rule(owner: User) -> DetectionRule:
    return DetectionRule(
        id=uuid.uuid4(),
        organization_id=owner.organization_id,
        slug="repeated-authentication-failure",
        name="Repeated authentication failures",
        description="Three failures for one actor.",
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
    )


def alert(owner: User, detection: DetectionRule, evidence: list[Event]) -> Alert:
    return Alert(
        id=uuid.uuid4(),
        organization_id=owner.organization_id,
        rule_id=detection.id,
        rule_version=detection.version,
        dedup_key="a" * 64,
        group_key="alice",
        status="open",
        severity="high",
        title=detection.name,
        summary="Rule matched three events.",
        event_count=len(evidence),
        evidence_event_ids=[str(item.id) for item in evidence],
        first_seen_at=evidence[0].observed_at,
        last_seen_at=evidence[-1].observed_at,
    )


def test_rule_schema_is_bounded_and_matches_canonical_fields() -> None:
    owner = user()
    item = event(owner)
    definition = RuleDefinition(
        conditions=[
            RuleCondition(field="category", operator="equals", value="AUTHENTICATION"),
            RuleCondition(field="title", operator="contains", value="failure"),
        ],
        group_by="actor",
        threshold=3,
        window_seconds=900,
    )
    assert event_matches(item, definition)
    assert event_group(item, definition) == "alice"
    assert len(alert_dedup_key(rule(owner), item, "alice")) == 64
    item.title = "Successful login"
    assert not event_matches(item, definition)
    with pytest.raises(ValidationError):
        RuleDefinition(
            conditions=[
                RuleCondition(field="title", operator="contains", value="failure"),
                RuleCondition(field="title", operator="contains", value="failure"),
            ]
        )


async def test_evaluation_threshold_creates_and_updates_a_deduplicated_alert() -> None:
    owner = user()
    detection = rule(owner)
    evidence = [event(owner) for _ in range(3)]
    evidence[0].observed_at = datetime(2026, 7, 24, 9, 50, tzinfo=UTC)
    db = database()
    db.scalars.side_effect = [[detection], evidence]
    db.scalar.return_value = None
    produced = await evaluate_event(db, evidence[-1])
    assert len(produced) == 1
    db.add.assert_called_once()
    created = db.add.call_args.args[0]
    assert created.event_count == 3
    assert created.rule_version == 1

    existing = alert(owner, detection, evidence[:1])
    db = database()
    db.scalars.side_effect = [[detection], evidence]
    db.scalar.return_value = existing
    assert await evaluate_event(db, evidence[-1]) == [existing]
    assert existing.event_count == 3
    db.add.assert_not_called()


async def test_evaluation_below_threshold_produces_nothing() -> None:
    owner = user()
    db = database()
    db.scalars.side_effect = [[rule(owner)], [event(owner)]]
    assert await evaluate_event(db, event(owner)) == []


async def test_webhook_authentication_and_queue_limits() -> None:
    db = database()
    with pytest.raises(HTTPException) as missing:
        await enqueue_webhook(WebhookBatch(events=[{}]), db, None)
    assert missing.value.status_code == 401
    db.scalar.return_value = None
    with pytest.raises(HTTPException) as invalid:
        await enqueue_webhook(WebhookBatch(events=[{}]), db, "invalid-key-value")
    assert invalid.value.status_code == 401

    source = IngestionSource(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        name="Test",
        token_hash=token_digest("valid-ingestion-key"),
        enabled=True,
    )
    db.scalar.return_value = source
    db.commit.side_effect = lambda: setattr(db.add.call_args.args[0], "id", uuid.uuid4())
    result = await enqueue_webhook(
        WebhookBatch(events=[{"title": "Safe"}]), db, "valid-ingestion-key"
    )
    assert result.received == 1
    assert result.status == "queued"

    with pytest.raises(ValidationError):
        WebhookBatch(events=[])


async def test_job_processing_completes_or_records_safe_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner = user()
    valid = IngestionJob(
        id=uuid.uuid4(),
        organization_id=owner.organization_id,
        source_id=uuid.uuid4(),
        status="processing",
        payload=[
            {
                "title": "Authentication failure",
                "severity": "high",
                "observed_at": "2026-07-24T10:00:00Z",
            }
        ],
        received_count=1,
        imported_count=0,
    )
    db = database()
    evaluation = AsyncMock(return_value=[])
    monkeypatch.setattr("app.ingestion.evaluate_event", evaluation)
    assert await process_job(db, valid) == 1
    assert valid.status == "completed"
    evaluation.assert_awaited_once()

    invalid = IngestionJob(
        id=uuid.uuid4(),
        organization_id=owner.organization_id,
        source_id=uuid.uuid4(),
        status="processing",
        payload=[{"severity": "dramatic"}],
        received_count=1,
        imported_count=0,
    )
    assert await process_job(database(), invalid) == 0
    assert invalid.status == "failed"
    assert invalid.error_code == "invalid_event"


async def test_claim_next_job_marks_processing() -> None:
    db = database()
    db.scalar.return_value = None
    assert await claim_next_job(db) is None
    job = Mock(spec=IngestionJob)
    job.status = "queued"
    db.scalar.return_value = job
    assert await claim_next_job(db) is job
    assert job.status == "processing"
    db.commit.assert_awaited_once()


async def test_rule_and_alert_apis_are_tenant_scoped() -> None:
    owner = user()
    detection = rule(owner)
    evidence = [event(owner) for _ in range(3)]
    finding = alert(owner, detection, evidence)
    db = database()
    db.scalars.return_value = [detection]
    rules = await list_rules(owner, db)
    assert rules[0].definition.threshold == 3

    db.scalar.return_value = 1
    db.scalars.return_value = [finding]
    page = await list_alerts(owner, db, "open", "high", 1, 25)
    assert page.total == 1
    assert page.items[0].status == "open"

    db.scalar.side_effect = [finding, detection]
    db.scalars.return_value = evidence
    detail = await alert_detail(finding.id, owner, db)
    assert detail.rule.slug == detection.slug
    assert len(detail.evidence) == 3


async def test_alert_detail_and_state_changes_fail_closed() -> None:
    owner = user()
    db = database()
    db.scalar.return_value = None
    with pytest.raises(HTTPException) as missing:
        await alert_detail(uuid.uuid4(), owner, db)
    assert missing.value.status_code == 404
    with pytest.raises(HTTPException) as state_missing:
        await change_alert_status(uuid.uuid4(), AlertStateChange(status="resolved"), owner, db)
    assert state_missing.value.status_code == 404

    finding = alert(owner, rule(owner), [event(owner)])
    db.scalar.return_value = finding
    updated = await change_alert_status(
        finding.id, AlertStateChange(status="acknowledged"), owner, db
    )
    assert updated.status == "acknowledged"
    db.commit.assert_awaited_once()
