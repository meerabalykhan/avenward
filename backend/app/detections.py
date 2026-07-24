"""Deterministic, data-only detection rules and evidence-backed alert creation."""

import hashlib
from datetime import timedelta
from typing import Literal

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, DetectionRule, Event


class RuleCondition(BaseModel):
    field: Literal["source", "category", "severity", "title", "actor", "target"]
    operator: Literal["equals", "contains"]
    value: str = Field(min_length=1, max_length=240)


class RuleDefinition(BaseModel):
    conditions: list[RuleCondition] = Field(min_length=1, max_length=10)
    group_by: Literal["source", "category", "severity", "actor", "target"] | None = None
    threshold: int = Field(default=1, ge=1, le=1000)
    window_seconds: int = Field(default=300, ge=60, le=86400)

    @field_validator("conditions")
    @classmethod
    def unique_conditions(cls, value: list[RuleCondition]) -> list[RuleCondition]:
        if len({(item.field, item.operator, item.value.lower()) for item in value}) != len(value):
            raise ValueError("duplicate conditions are not allowed")
        return value


def definition_for(rule: DetectionRule) -> RuleDefinition:
    return RuleDefinition.model_validate(
        {
            "conditions": rule.conditions,
            "group_by": rule.group_by,
            "threshold": rule.threshold,
            "window_seconds": rule.window_seconds,
        }
    )


def event_matches(event: Event, definition: RuleDefinition) -> bool:
    for condition in definition.conditions:
        candidate = getattr(event, condition.field) or ""
        candidate_text = str(candidate).lower()
        expected = condition.value.lower()
        if condition.operator == "equals" and candidate_text != expected:
            return False
        if condition.operator == "contains" and expected not in candidate_text:
            return False
    return True


def event_group(event: Event, definition: RuleDefinition) -> str:
    if definition.group_by is None:
        return "all"
    return str(getattr(event, definition.group_by) or "unknown")[:240]


def alert_dedup_key(rule: DetectionRule, event: Event, group_key: str) -> str:
    bucket = int(event.observed_at.timestamp()) // rule.window_seconds
    material = f"{event.organization_id}:{rule.id}:{rule.version}:{group_key.lower()}:{bucket}"
    return hashlib.sha256(material.encode()).hexdigest()


async def evaluate_event(db: AsyncSession, event: Event) -> list[Alert]:
    """Evaluate enabled tenant rules without executing user-supplied code."""

    rules = list(
        await db.scalars(
            select(DetectionRule).where(
                DetectionRule.organization_id == event.organization_id,
                DetectionRule.enabled.is_(True),
            )
        )
    )
    produced: list[Alert] = []
    for rule in rules:
        definition = definition_for(rule)
        if not event_matches(event, definition):
            continue
        group_key = event_group(event, definition)
        candidates = list(
            await db.scalars(
                select(Event).where(
                    Event.organization_id == event.organization_id,
                    Event.observed_at >= event.observed_at - timedelta(seconds=rule.window_seconds),
                    Event.observed_at <= event.observed_at,
                )
            )
        )
        evidence = [
            item
            for item in candidates
            if event_matches(item, definition) and event_group(item, definition) == group_key
        ]
        if len(evidence) < rule.threshold:
            continue
        evidence.sort(key=lambda item: (item.observed_at, str(item.id)))
        evidence = evidence[-50:]
        dedup_key = alert_dedup_key(rule, event, group_key)
        alert = await db.scalar(select(Alert).where(Alert.dedup_key == dedup_key))
        evidence_ids = [str(item.id) for item in evidence]
        if alert is None:
            alert = Alert(
                organization_id=event.organization_id,
                rule_id=rule.id,
                rule_version=rule.version,
                dedup_key=dedup_key,
                group_key=group_key,
                status="open",
                severity=rule.severity,
                title=rule.name,
                summary=(
                    f"Rule {rule.slug} v{rule.version} matched {len(evidence)} events "
                    f"for {group_key} within {rule.window_seconds} seconds."
                ),
                event_count=len(evidence),
                evidence_event_ids=evidence_ids,
                first_seen_at=evidence[0].observed_at,
                last_seen_at=evidence[-1].observed_at,
            )
            db.add(alert)
        else:
            alert.event_count = len(evidence)
            alert.evidence_event_ids = evidence_ids
            alert.first_seen_at = evidence[0].observed_at
            alert.last_seen_at = evidence[-1].observed_at
        produced.append(alert)
    return produced
