# ADR 0002: Use PostgreSQL as the durable system of record

- Status: Accepted
- Date: 2026-07-23

## Decision

Use PostgreSQL with UUID keys, timezone-aware timestamps, foreign keys,
constraints, and Alembic migrations. Tenant-owned access is always scoped by
organization.

## Consequences

Relational integrity and expressive indexed search suit the initial workload.
JSON fields remain available for evolving event attributes. Partitioning and a
specialized search store are deferred until repeatable benchmarks require them.
