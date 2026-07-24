import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.v1.findings import (
    FindingImportBatch,
    FindingImportItem,
    FindingStateChange,
    change_finding_status,
    finding_detail,
    finding_view,
    import_findings,
    list_findings,
)
from app.api.v1.investigations import (
    CommentCreate,
    InvestigationCreate,
    InvestigationUpdate,
    LinkCreate,
    add_comment,
    add_link,
    create_investigation,
    evidence_label,
    investigation_detail,
    list_investigations,
    owned_investigation,
    update_investigation,
    validate_owner,
)
from app.audit import record_audit
from app.models import (
    AuditRecord,
    Investigation,
    InvestigationComment,
    InvestigationLink,
    User,
    VulnerabilityFinding,
)

NOW = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)


def database() -> Mock:
    db = Mock()
    db.scalar = AsyncMock()
    db.scalars = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    async def flush() -> None:
        item = db.add.call_args.args[0]
        if getattr(item, "id", None) is None:
            item.id = uuid.uuid4()
        if hasattr(item, "created_at") and getattr(item, "created_at", None) is None:
            item.created_at = NOW
        if hasattr(item, "updated_at") and getattr(item, "updated_at", None) is None:
            item.updated_at = NOW

    db.flush = AsyncMock(side_effect=flush)
    return db


def analyst() -> User:
    return User(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        email="analyst@example.com",
        display_name="Analyst",
        password_hash="unused",
        role="admin",
    )


def finding(owner: User) -> VulnerabilityFinding:
    return VulnerabilityFinding(
        id=uuid.uuid4(),
        organization_id=owner.organization_id,
        source="demo-scanner",
        external_id="finding-1",
        asset_identifier="web-01",
        title="Outdated component",
        severity="high",
        cvss_score_tenths=81,
        cve="CVE-2025-0001",
        description="A supported synthetic finding.",
        remediation="Test and deploy the supported update.",
        evidence={"synthetic": True},
        status="open",
        exception_reason=None,
        first_seen_at=NOW - timedelta(days=1),
        last_seen_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )


def investigation(owner: User) -> Investigation:
    return Investigation(
        id=uuid.uuid4(),
        organization_id=owner.organization_id,
        title="Review exposure",
        summary="Determine scope and document an approved response.",
        severity="high",
        status="open",
        owner_id=owner.id,
        resolution=None,
        created_by_id=owner.id,
        created_at=NOW,
        updated_at=NOW,
        resolved_at=None,
    )


def import_item(**changes: object) -> FindingImportItem:
    values: dict[str, object] = {
        "external_id": "finding-1",
        "source": "demo-scanner",
        "asset_identifier": "web-01",
        "title": "Outdated component",
        "severity": "high",
        "cvss_score": 8.1,
        "cve": "CVE-2025-0001",
        "description": "Synthetic scanner evidence.",
        "remediation": "Test and deploy the supported update.",
        "evidence": {"synthetic": True},
        "first_seen_at": NOW - timedelta(days=1),
        "last_seen_at": NOW,
    }
    values.update(changes)
    return FindingImportItem.model_validate(values)


def test_finding_input_rejects_unsafe_or_inconsistent_shapes() -> None:
    assert import_item().cvss_score == 8.1
    with pytest.raises(ValidationError):
        import_item(title="   ")
    with pytest.raises(ValidationError):
        import_item(last_seen_at=NOW - timedelta(days=2))
    with pytest.raises(ValidationError):
        import_item(evidence={"value": "x" * 33_000})
    with pytest.raises(ValidationError):
        FindingImportBatch(findings=[])
    with pytest.raises(ValidationError):
        FindingStateChange(status="accepted")


async def test_import_findings_creates_and_refreshes_with_audit() -> None:
    user = analyst()
    db = database()
    db.scalar.side_effect = [None, finding(user)]
    result = await import_findings(
        FindingImportBatch(findings=[import_item(), import_item(title="Refreshed title")]), user, db
    )
    assert result == {"created": 1, "updated": 1}
    assert db.add.call_count == 3
    db.commit.assert_awaited_once()


async def test_finding_queries_and_state_are_tenant_scoped() -> None:
    user = analyst()
    item = finding(user)
    db = database()
    db.scalar.return_value = 1
    db.scalars.return_value = [item]
    page = await list_findings(user, db, "web", "open", "high", 1, 25)
    assert page.total == 1
    assert page.items[0].cvss_score == 8.1
    assert "organization_id" in str(db.scalar.await_args.args[0])

    db.scalar.return_value = item
    assert (await finding_detail(item.id, user, db)).title == item.title
    updated = await change_finding_status(
        item.id,
        FindingStateChange(status="accepted", exception_reason="Compensating control"),
        user,
        db,
    )
    assert updated.status == "accepted"
    assert updated.exception_reason == "Compensating control"

    db.scalar.return_value = None
    with pytest.raises(HTTPException) as missing:
        await finding_detail(uuid.uuid4(), user, db)
    assert missing.value.status_code == 404
    assert finding_view(item).external_id == "finding-1"


def test_record_audit_is_append_only_data() -> None:
    user = analyst()
    db = database()
    entity_id = uuid.uuid4()
    record = record_audit(db, user, "investigation", entity_id, "case.test", {"safe": True})
    assert record.organization_id == user.organization_id
    assert record.details == {"safe": True}
    db.add.assert_called_once_with(record)


async def test_investigation_create_list_update_and_owner_validation() -> None:
    user = analyst()
    db = database()
    db.scalar.return_value = user
    created = await create_investigation(
        InvestigationCreate(
            title="Review exposure",
            summary="Validate the finding.",
            severity="high",
            owner_id=user.id,
        ),
        user,
        db,
    )
    assert created.status == "open"

    item = investigation(user)
    db.scalar.return_value = 1
    db.scalars.return_value = [item]
    page = await list_investigations(user, db, "open", 1, 25)
    assert page.total == 1

    db.scalar.side_effect = [item, user]
    updated = await update_investigation(
        item.id,
        InvestigationUpdate(status="resolved", owner_id=user.id, resolution="Patched safely."),
        user,
        db,
    )
    assert updated.status == "resolved"
    assert updated.resolved_at is not None
    db.refresh.assert_awaited_once_with(item)

    with pytest.raises(ValidationError):
        InvestigationUpdate(status="resolved")
    db.scalar.side_effect = None
    db.scalar.return_value = None
    await validate_owner(None, user, db)
    with pytest.raises(HTTPException):
        await validate_owner(uuid.uuid4(), user, db)


async def test_links_comments_and_detail_preserve_history() -> None:
    user = analyst()
    item = investigation(user)
    evidence = finding(user)
    db = database()
    db.scalar.side_effect = [item, evidence, None]
    link_view = await add_link(
        item.id, LinkCreate(entity_type="finding", entity_id=evidence.id), user, db
    )
    assert link_view.label == evidence.title

    db.scalar.side_effect = [item]
    comment = await add_comment(item.id, CommentCreate(body="  Analyst note.  "), user, db)
    assert comment.body == "Analyst note."

    link = InvestigationLink(
        id=uuid.uuid4(),
        organization_id=user.organization_id,
        investigation_id=item.id,
        entity_type="finding",
        entity_id=evidence.id,
        created_by_id=user.id,
        created_at=NOW,
    )
    note = InvestigationComment(
        id=uuid.uuid4(),
        organization_id=user.organization_id,
        investigation_id=item.id,
        author_id=user.id,
        body="Analyst note.",
        created_at=NOW,
    )
    audit = AuditRecord(
        id=uuid.uuid4(),
        organization_id=user.organization_id,
        actor_id=user.id,
        entity_type="investigation",
        entity_id=item.id,
        action="investigation.created",
        details={},
        created_at=NOW,
    )
    db.scalar.side_effect = [item, evidence]
    db.scalars.side_effect = [[link], [note], [audit]]
    detail = await investigation_detail(item.id, user, db)
    assert detail.links[0].label == evidence.title
    assert detail.comments[0].body == "Analyst note."
    assert detail.audit[0].action == "investigation.created"


async def test_missing_or_duplicate_investigation_evidence_fails_closed() -> None:
    user = analyst()
    item = investigation(user)
    db = database()
    db.scalar.return_value = None
    with pytest.raises(HTTPException) as missing:
        await owned_investigation(item.id, user, db)
    assert missing.value.status_code == 404

    with pytest.raises(HTTPException):
        await evidence_label("finding", uuid.uuid4(), user, db)

    db.scalar.side_effect = [item, finding(user), Mock(spec=InvestigationLink)]
    with pytest.raises(HTTPException) as duplicate:
        await add_link(
            item.id,
            LinkCreate(entity_type="finding", entity_id=uuid.uuid4()),
            user,
            db,
        )
    assert duplicate.value.status_code == 409
