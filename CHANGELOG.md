# Changelog

## [0.3.0] - 2026-07-24

### Added

- Imported vulnerability findings with assets, CVSS metadata, evidence, and guidance
- Investigation creation, ownership, evidence linking, comments, and resolution
- Append-only audit history for finding and investigation changes
- Investigation and vulnerability workflows in the analyst workspace
- Phase 3 database migration, synthetic case, tests, and validation guide

### Security

- Finding imports enforce bounded records, text, CVSS values, timestamps, and evidence size
- Evidence links and owners must belong to the active organization
- Resolution requires an explicit analyst record and never alters linked evidence
- Imported scanner content is stored and displayed as untrusted data, never executed

## [0.2.0] - 2026-07-24

### Added

- Authenticated, bounded webhook ingestion backed by durable database jobs
- Background worker for normalization and deterministic rule evaluation
- Versioned, declarative detection rules with restricted fields and operators
- Tenant-scoped, evidence-backed alert creation and time-bucket deduplication
- Alert rationale, supporting evidence, and open/acknowledged/resolved workflow
- Phase 2 migration, validation guide, and expanded defensive platform roadmap

### Security

- Ingestion credentials are stored as SHA-256 digests
- Malformed batches fail without partially importing evidence
- Rules are interpreted as bounded data and cannot execute user-supplied code
- Alert state transitions preserve their original evidence and rule version

## [0.1.0] - 2026-07-23

### Added

- Local demo authentication with hashed passwords and revocable opaque sessions
- Tenant-scoped PostgreSQL models and Alembic migration
- Safe CSV, JSON, and JSONL preview/import with explicit limits
- Canonical event overview, search, pagination, and detail
- Deterministic synthetic evidence generator and analyst workspace

### Security

- Session tokens are stored only as SHA-256 digests
- Event repositories scope reads and writes by organization
- Upload content is bounded, decoded as UTF-8, validated, and never executed

All notable changes follow [Keep a Changelog](https://keepachangelog.com/) and
semantic versioning.

## [Unreleased]

## [0.0.1] - 2026-07-23

### Added

- Initial product, architecture, security, roadmap, limitation, and ADR documents
- FastAPI health, readiness, and version endpoints
- React and TypeScript landing shell
- PostgreSQL, Redis, Nginx, and Docker Compose development scaffolding
- Initial automated tests and CI quality checks
- Open-source community and licensing files
