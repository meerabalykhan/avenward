"""Safe vulnerability-finding import, search, detail, and state APIs."""

import json
import uuid
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import func, or_, select

from app.api.v1.auth import CurrentUser, DatabaseSession
from app.audit import record_audit
from app.models import VulnerabilityFinding

router = APIRouter(prefix="/findings", tags=["findings"])

Severity = Literal["informational", "low", "medium", "high", "critical"]
FindingStatus = Literal["open", "accepted", "resolved"]


class FindingImportItem(BaseModel):
    external_id: str = Field(min_length=1, max_length=160)
    source: str = Field(min_length=1, max_length=80)
    asset_identifier: str = Field(min_length=1, max_length=240)
    title: str = Field(min_length=1, max_length=240)
    severity: Severity
    cvss_score: float | None = Field(default=None, ge=0, le=10)
    cve: str | None = Field(default=None, max_length=40, pattern=r"^CVE-\d{4}-\d{4,}$")
    description: str = Field(min_length=1, max_length=8000)
    remediation: str = Field(min_length=1, max_length=8000)
    evidence: dict[str, object] = Field(default_factory=dict)
    first_seen_at: datetime
    last_seen_at: datetime

    @field_validator("source", "asset_identifier", "title", "description", "remediation")
    @classmethod
    def clean_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must contain visible characters")
        return cleaned

    @model_validator(mode="after")
    def safe_shape(self) -> "FindingImportItem":
        if self.last_seen_at < self.first_seen_at:
            raise ValueError("last_seen_at must not precede first_seen_at")
        if len(json.dumps(self.evidence, default=str)) > 32_768:
            raise ValueError("evidence exceeds 32 KB")
        return self


class FindingImportBatch(BaseModel):
    findings: list[FindingImportItem] = Field(min_length=1, max_length=500)


class FindingView(BaseModel):
    id: uuid.UUID
    source: str
    external_id: str
    asset_identifier: str
    title: str
    severity: str
    cvss_score: float | None
    cve: str | None
    description: str
    remediation: str
    status: str
    exception_reason: str | None
    first_seen_at: datetime
    last_seen_at: datetime


class FindingPage(BaseModel):
    items: list[FindingView]
    page: int
    page_size: int
    total: int


class FindingStateChange(BaseModel):
    status: FindingStatus
    exception_reason: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def require_exception_reason(self) -> "FindingStateChange":
        if self.status == "accepted" and not (self.exception_reason or "").strip():
            raise ValueError("accepted findings require an exception reason")
        return self


def finding_view(item: VulnerabilityFinding) -> FindingView:
    return FindingView(
        id=item.id,
        source=item.source,
        external_id=item.external_id,
        asset_identifier=item.asset_identifier,
        title=item.title,
        severity=item.severity,
        cvss_score=(item.cvss_score_tenths / 10 if item.cvss_score_tenths is not None else None),
        cve=item.cve,
        description=item.description,
        remediation=item.remediation,
        status=item.status,
        exception_reason=item.exception_reason,
        first_seen_at=item.first_seen_at,
        last_seen_at=item.last_seen_at,
    )


@router.post("/import", status_code=status.HTTP_201_CREATED)
async def import_findings(
    payload: FindingImportBatch, user: CurrentUser, db: DatabaseSession
) -> dict[str, int]:
    created = 0
    updated = 0
    for incoming in payload.findings:
        finding = await db.scalar(
            select(VulnerabilityFinding).where(
                VulnerabilityFinding.organization_id == user.organization_id,
                VulnerabilityFinding.source == incoming.source,
                VulnerabilityFinding.external_id == incoming.external_id,
            )
        )
        values = incoming.model_dump(exclude={"cvss_score"})
        values["cvss_score_tenths"] = (
            round(incoming.cvss_score * 10) if incoming.cvss_score is not None else None
        )
        if finding is None:
            finding = VulnerabilityFinding(
                organization_id=user.organization_id,
                status="open",
                exception_reason=None,
                **values,
            )
            db.add(finding)
            await db.flush()
            record_audit(
                db, user, "finding", finding.id, "finding.imported", {"source": incoming.source}
            )
            created += 1
        else:
            for key, value in values.items():
                setattr(finding, key, value)
            record_audit(
                db, user, "finding", finding.id, "finding.refreshed", {"source": incoming.source}
            )
            updated += 1
    await db.commit()
    return {"created": created, "updated": updated}


@router.get("", response_model=FindingPage)
async def list_findings(
    user: CurrentUser,
    db: DatabaseSession,
    q: Annotated[str | None, Query(max_length=120)] = None,
    state: Annotated[str | None, Query(alias="status")] = None,
    severity: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> FindingPage:
    filters = [VulnerabilityFinding.organization_id == user.organization_id]
    if state:
        filters.append(VulnerabilityFinding.status == state.lower())
    if severity:
        filters.append(VulnerabilityFinding.severity == severity.lower())
    if q:
        pattern = f"%{q}%"
        filters.append(
            or_(
                VulnerabilityFinding.title.ilike(pattern),
                VulnerabilityFinding.asset_identifier.ilike(pattern),
                VulnerabilityFinding.cve.ilike(pattern),
            )
        )
    total = (
        await db.scalar(select(func.count()).select_from(VulnerabilityFinding).where(*filters)) or 0
    )
    rows = await db.scalars(
        select(VulnerabilityFinding)
        .where(*filters)
        .order_by(VulnerabilityFinding.last_seen_at.desc(), VulnerabilityFinding.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return FindingPage(
        items=[finding_view(item) for item in rows], page=page, page_size=page_size, total=total
    )


async def owned_finding(
    finding_id: uuid.UUID, user: CurrentUser, db: DatabaseSession
) -> VulnerabilityFinding:
    finding = await db.scalar(
        select(VulnerabilityFinding).where(
            VulnerabilityFinding.id == finding_id,
            VulnerabilityFinding.organization_id == user.organization_id,
        )
    )
    if finding is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Finding not found")
    return finding


@router.get("/{finding_id}", response_model=FindingView)
async def finding_detail(
    finding_id: uuid.UUID, user: CurrentUser, db: DatabaseSession
) -> FindingView:
    return finding_view(await owned_finding(finding_id, user, db))


@router.patch("/{finding_id}/status", response_model=FindingView)
async def change_finding_status(
    finding_id: uuid.UUID,
    payload: FindingStateChange,
    user: CurrentUser,
    db: DatabaseSession,
) -> FindingView:
    finding = await owned_finding(finding_id, user, db)
    previous = finding.status
    finding.status = payload.status
    finding.exception_reason = (
        payload.exception_reason.strip() if payload.exception_reason else None
    )
    record_audit(
        db,
        user,
        "finding",
        finding.id,
        "finding.status_changed",
        {"from": previous, "to": payload.status},
    )
    await db.commit()
    return finding_view(finding)
