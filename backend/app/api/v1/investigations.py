"""Tenant-scoped investigation, evidence-link, comment, and audit APIs."""

import uuid
from datetime import UTC, datetime
from typing import Annotated, Literal, cast

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select

from app.api.v1.auth import CurrentUser, DatabaseSession
from app.audit import record_audit
from app.models import (
    Alert,
    AuditRecord,
    Event,
    Investigation,
    InvestigationComment,
    InvestigationLink,
    User,
    VulnerabilityFinding,
)

router = APIRouter(prefix="/investigations", tags=["investigations"])

Severity = Literal["informational", "low", "medium", "high", "critical"]
InvestigationStatus = Literal["open", "in_progress", "resolved"]
EntityType = Literal["alert", "event", "finding"]


class InvestigationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    summary: str = Field(min_length=1, max_length=8000)
    severity: Severity
    owner_id: uuid.UUID | None = None


class InvestigationUpdate(BaseModel):
    status: InvestigationStatus | None = None
    severity: Severity | None = None
    owner_id: uuid.UUID | None = None
    resolution: str | None = Field(default=None, max_length=8000)

    @model_validator(mode="after")
    def resolved_requires_resolution(self) -> "InvestigationUpdate":
        if self.status == "resolved" and not (self.resolution or "").strip():
            raise ValueError("resolved investigations require a resolution")
        return self


class LinkCreate(BaseModel):
    entity_type: EntityType
    entity_id: uuid.UUID


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=8000)


class InvestigationView(BaseModel):
    id: uuid.UUID
    title: str
    summary: str
    severity: str
    status: str
    owner_id: uuid.UUID | None
    resolution: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvestigationPage(BaseModel):
    items: list[InvestigationView]
    page: int
    page_size: int
    total: int


class LinkView(BaseModel):
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    label: str
    created_at: datetime


class CommentView(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditView(BaseModel):
    id: uuid.UUID
    actor_id: uuid.UUID
    action: str
    details: dict[str, object]
    created_at: datetime

    model_config = {"from_attributes": True}


class InvestigationDetail(InvestigationView):
    links: list[LinkView]
    comments: list[CommentView]
    audit: list[AuditView]


async def owned_investigation(
    investigation_id: uuid.UUID, user: CurrentUser, db: DatabaseSession
) -> Investigation:
    item = await db.scalar(
        select(Investigation).where(
            Investigation.id == investigation_id,
            Investigation.organization_id == user.organization_id,
        )
    )
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Investigation not found")
    return item


async def validate_owner(
    owner_id: uuid.UUID | None, user: CurrentUser, db: DatabaseSession
) -> None:
    if owner_id is None:
        return
    owner = await db.scalar(
        select(User).where(User.id == owner_id, User.organization_id == user.organization_id)
    )
    if owner is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Owner is unavailable")


async def evidence_label(
    entity_type: EntityType, entity_id: uuid.UUID, user: CurrentUser, db: DatabaseSession
) -> str:
    if entity_type == "alert":
        entity = await db.scalar(
            select(Alert).where(
                Alert.id == entity_id, Alert.organization_id == user.organization_id
            )
        )
    elif entity_type == "event":
        entity = await db.scalar(
            select(Event).where(
                Event.id == entity_id, Event.organization_id == user.organization_id
            )
        )
    else:
        entity = await db.scalar(
            select(VulnerabilityFinding).where(
                VulnerabilityFinding.id == entity_id,
                VulnerabilityFinding.organization_id == user.organization_id,
            )
        )
    if entity is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Evidence is unavailable")
    return str(entity.title)


@router.post("", response_model=InvestigationView, status_code=status.HTTP_201_CREATED)
async def create_investigation(
    payload: InvestigationCreate, user: CurrentUser, db: DatabaseSession
) -> Investigation:
    await validate_owner(payload.owner_id, user, db)
    item = Investigation(
        organization_id=user.organization_id,
        created_by_id=user.id,
        status="open",
        resolution=None,
        **payload.model_dump(),
    )
    db.add(item)
    await db.flush()
    record_audit(db, user, "investigation", item.id, "investigation.created")
    await db.commit()
    return item


@router.get("", response_model=InvestigationPage)
async def list_investigations(
    user: CurrentUser,
    db: DatabaseSession,
    state: Annotated[str | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> InvestigationPage:
    filters = [Investigation.organization_id == user.organization_id]
    if state:
        filters.append(Investigation.status == state.lower())
    total = await db.scalar(select(func.count()).select_from(Investigation).where(*filters)) or 0
    rows = await db.scalars(
        select(Investigation)
        .where(*filters)
        .order_by(Investigation.updated_at.desc(), Investigation.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return InvestigationPage(items=list(rows), page=page, page_size=page_size, total=total)


@router.patch("/{investigation_id}", response_model=InvestigationView)
async def update_investigation(
    investigation_id: uuid.UUID,
    payload: InvestigationUpdate,
    user: CurrentUser,
    db: DatabaseSession,
) -> Investigation:
    item = await owned_investigation(investigation_id, user, db)
    if "owner_id" in payload.model_fields_set:
        await validate_owner(payload.owner_id, user, db)
    changes: dict[str, object] = {}
    for field, value in payload.model_dump(exclude_unset=True).items():
        previous = getattr(item, field)
        if previous != value:
            changes[field] = {
                "from": str(previous) if previous is not None else None,
                "to": str(value) if value is not None else None,
            }
            setattr(item, field, value.strip() if field == "resolution" and value else value)
    if payload.status == "resolved":
        item.resolved_at = datetime.now(UTC)
    elif payload.status is not None:
        item.resolved_at = None
    if changes:
        record_audit(db, user, "investigation", item.id, "investigation.updated", changes)
    await db.commit()
    # PostgreSQL computes ``updated_at`` during the UPDATE. Refresh the model
    # before FastAPI serializes it so SQLAlchemy does not attempt async lazy
    # loading from the synchronous response-validation path.
    await db.refresh(item)
    return item


@router.post(
    "/{investigation_id}/links", response_model=LinkView, status_code=status.HTTP_201_CREATED
)
async def add_link(
    investigation_id: uuid.UUID,
    payload: LinkCreate,
    user: CurrentUser,
    db: DatabaseSession,
) -> LinkView:
    await owned_investigation(investigation_id, user, db)
    label = await evidence_label(payload.entity_type, payload.entity_id, user, db)
    existing = await db.scalar(
        select(InvestigationLink).where(
            InvestigationLink.investigation_id == investigation_id,
            InvestigationLink.entity_type == payload.entity_type,
            InvestigationLink.entity_id == payload.entity_id,
        )
    )
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Evidence is already linked")
    link = InvestigationLink(
        organization_id=user.organization_id,
        investigation_id=investigation_id,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        created_by_id=user.id,
    )
    db.add(link)
    await db.flush()
    record_audit(
        db,
        user,
        "investigation",
        investigation_id,
        "evidence.linked",
        {"type": payload.entity_type, "id": str(payload.entity_id)},
    )
    await db.commit()
    return LinkView(
        id=link.id,
        entity_type=link.entity_type,
        entity_id=link.entity_id,
        label=label,
        created_at=link.created_at,
    )


@router.post(
    "/{investigation_id}/comments", response_model=CommentView, status_code=status.HTTP_201_CREATED
)
async def add_comment(
    investigation_id: uuid.UUID,
    payload: CommentCreate,
    user: CurrentUser,
    db: DatabaseSession,
) -> InvestigationComment:
    await owned_investigation(investigation_id, user, db)
    comment = InvestigationComment(
        organization_id=user.organization_id,
        investigation_id=investigation_id,
        author_id=user.id,
        body=payload.body.strip(),
    )
    db.add(comment)
    await db.flush()
    record_audit(
        db,
        user,
        "investigation",
        investigation_id,
        "comment.added",
        {"comment_id": str(comment.id)},
    )
    await db.commit()
    return comment


@router.get("/{investigation_id}", response_model=InvestigationDetail)
async def investigation_detail(
    investigation_id: uuid.UUID, user: CurrentUser, db: DatabaseSession
) -> InvestigationDetail:
    item = await owned_investigation(investigation_id, user, db)
    links = list(
        await db.scalars(
            select(InvestigationLink)
            .where(
                InvestigationLink.investigation_id == item.id,
                InvestigationLink.organization_id == user.organization_id,
            )
            .order_by(InvestigationLink.created_at)
        )
    )
    link_views = [
        LinkView(
            id=link.id,
            entity_type=link.entity_type,
            entity_id=link.entity_id,
            label=await evidence_label(
                cast(EntityType, link.entity_type), link.entity_id, user, db
            ),
            created_at=link.created_at,
        )
        for link in links
    ]
    comments = list(
        await db.scalars(
            select(InvestigationComment)
            .where(
                InvestigationComment.investigation_id == item.id,
                InvestigationComment.organization_id == user.organization_id,
            )
            .order_by(InvestigationComment.created_at)
        )
    )
    audit = list(
        await db.scalars(
            select(AuditRecord)
            .where(
                AuditRecord.organization_id == user.organization_id,
                AuditRecord.entity_type == "investigation",
                AuditRecord.entity_id == item.id,
            )
            .order_by(AuditRecord.created_at)
        )
    )
    return InvestigationDetail(
        **InvestigationView.model_validate(item).model_dump(),
        links=link_views,
        comments=comments,
        audit=audit,
    )
