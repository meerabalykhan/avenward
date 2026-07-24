"""Tenant-scoped rules, alert list, evidence detail, and state transitions."""

import uuid
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.v1.auth import CurrentUser, DatabaseSession
from app.detections import RuleDefinition, definition_for
from app.models import Alert, DetectionRule, Event

router = APIRouter(tags=["detections"])


class RuleView(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str
    version: int
    enabled: bool
    severity: str
    definition: RuleDefinition


class AlertView(BaseModel):
    id: uuid.UUID
    status: str
    severity: str
    title: str
    summary: str
    group_key: str
    rule_version: int
    event_count: int
    first_seen_at: datetime
    last_seen_at: datetime

    model_config = {"from_attributes": True}


class AlertPage(BaseModel):
    items: list[AlertView]
    page: int
    page_size: int
    total: int


class AlertDetail(AlertView):
    rule: RuleView
    evidence: list[dict[str, object]]


class AlertStateChange(BaseModel):
    status: Literal["open", "acknowledged", "resolved"]


def rule_view(rule: DetectionRule) -> RuleView:
    return RuleView(
        id=rule.id,
        slug=rule.slug,
        name=rule.name,
        description=rule.description,
        version=rule.version,
        enabled=rule.enabled,
        severity=rule.severity,
        definition=definition_for(rule),
    )


@router.get("/rules", response_model=list[RuleView])
async def list_rules(user: CurrentUser, db: DatabaseSession) -> list[RuleView]:
    rules = await db.scalars(
        select(DetectionRule)
        .where(DetectionRule.organization_id == user.organization_id)
        .order_by(DetectionRule.name, DetectionRule.version.desc())
    )
    return [rule_view(rule) for rule in rules]


@router.get("/alerts", response_model=AlertPage)
async def list_alerts(
    user: CurrentUser,
    db: DatabaseSession,
    state: Annotated[str | None, Query(alias="status")] = None,
    severity: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> AlertPage:
    filters = [Alert.organization_id == user.organization_id]
    if state:
        filters.append(Alert.status == state.lower())
    if severity:
        filters.append(Alert.severity == severity.lower())
    total = await db.scalar(select(func.count()).select_from(Alert).where(*filters)) or 0
    rows = await db.scalars(
        select(Alert)
        .where(*filters)
        .order_by(Alert.last_seen_at.desc(), Alert.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return AlertPage(items=list(rows), page=page, page_size=page_size, total=total)


@router.get("/alerts/{alert_id}", response_model=AlertDetail)
async def alert_detail(alert_id: uuid.UUID, user: CurrentUser, db: DatabaseSession) -> AlertDetail:
    alert = await db.scalar(
        select(Alert).where(Alert.id == alert_id, Alert.organization_id == user.organization_id)
    )
    if alert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    rule = await db.scalar(
        select(DetectionRule).where(
            DetectionRule.id == alert.rule_id,
            DetectionRule.organization_id == user.organization_id,
        )
    )
    if rule is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Alert rule is unavailable")
    evidence_ids = [uuid.UUID(item) for item in alert.evidence_event_ids]
    evidence_rows = list(
        await db.scalars(
            select(Event)
            .where(Event.organization_id == user.organization_id, Event.id.in_(evidence_ids))
            .order_by(Event.observed_at)
        )
    )
    evidence = [
        {
            "id": str(item.id),
            "title": item.title,
            "source": item.source,
            "observed_at": item.observed_at.isoformat(),
        }
        for item in evidence_rows
    ]
    return AlertDetail(
        **AlertView.model_validate(alert).model_dump(), rule=rule_view(rule), evidence=evidence
    )


@router.patch("/alerts/{alert_id}/status", response_model=AlertView)
async def change_alert_status(
    alert_id: uuid.UUID,
    payload: AlertStateChange,
    user: CurrentUser,
    db: DatabaseSession,
) -> Alert:
    alert = await db.scalar(
        select(Alert).where(Alert.id == alert_id, Alert.organization_id == user.organization_id)
    )
    if alert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    alert.status = payload.status
    await db.commit()
    return alert
