"""Append-only audit helpers for material analyst actions."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditRecord, User


def record_audit(
    db: AsyncSession,
    user: User,
    entity_type: str,
    entity_id: uuid.UUID,
    action: str,
    details: dict[str, object] | None = None,
) -> AuditRecord:
    record = AuditRecord(
        organization_id=user.organization_id,
        actor_id=user.id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        details=details or {},
    )
    db.add(record)
    return record
