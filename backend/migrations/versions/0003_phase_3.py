"""Phase 3 vulnerability findings, investigations, and audit history."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_phase_3"
down_revision = "0002_phase_2"
branch_labels = None
depends_on = None


def _identity_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "vulnerability_findings",
        *_identity_columns(),
        sa.Column("source", sa.String(80), nullable=False),
        sa.Column("external_id", sa.String(160), nullable=False),
        sa.Column("asset_identifier", sa.String(240), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("cvss_score_tenths", sa.Integer()),
        sa.Column("cve", sa.String(40)),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("remediation", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("exception_reason", sa.Text()),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "organization_id", "source", "external_id", name="uq_finding_source_external"
        ),
    )
    op.create_index(
        "ix_vulnerability_findings_organization_id", "vulnerability_findings", ["organization_id"]
    )
    op.create_index(
        "ix_vulnerability_findings_asset_identifier", "vulnerability_findings", ["asset_identifier"]
    )
    op.create_index(
        "ix_findings_org_status_severity",
        "vulnerability_findings",
        ["organization_id", "status", "severity"],
    )

    op.create_table(
        "investigations",
        *_identity_columns(),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("resolution", sa.Text()),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_investigations_organization_id", "investigations", ["organization_id"])
    op.create_index(
        "ix_investigations_org_status_updated",
        "investigations",
        ["organization_id", "status", "updated_at"],
    )

    op.create_table(
        "investigation_links",
        *_identity_columns(),
        sa.Column(
            "investigation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("investigations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "investigation_id", "entity_type", "entity_id", name="uq_investigation_entity"
        ),
    )
    op.create_index(
        "ix_investigation_links_organization_id", "investigation_links", ["organization_id"]
    )
    op.create_index(
        "ix_investigation_links_investigation_id", "investigation_links", ["investigation_id"]
    )
    op.create_index(
        "ix_investigation_links_org_investigation",
        "investigation_links",
        ["organization_id", "investigation_id"],
    )

    op.create_table(
        "investigation_comments",
        *_identity_columns(),
        sa.Column(
            "investigation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("investigations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_investigation_comments_organization_id", "investigation_comments", ["organization_id"]
    )
    op.create_index(
        "ix_investigation_comments_investigation_id", "investigation_comments", ["investigation_id"]
    )

    op.create_table(
        "audit_records",
        *_identity_columns(),
        sa.Column(
            "actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(60), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_audit_records_organization_id", "audit_records", ["organization_id"])
    op.create_index(
        "ix_audit_org_entity_created",
        "audit_records",
        ["organization_id", "entity_type", "entity_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("audit_records")
    op.drop_table("investigation_comments")
    op.drop_table("investigation_links")
    op.drop_table("investigations")
    op.drop_table("vulnerability_findings")
