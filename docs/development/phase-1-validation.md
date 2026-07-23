# Phase 1 validation record

## Release candidate

- Version: `0.1.0`
- Scope: authenticated, tenant-scoped local event explorer
- Data: deterministic synthetic evidence only

## Implemented workflow

1. Docker applies the Alembic schema and idempotently seeds a local organization,
   analyst, and 36 deterministic synthetic events.
2. The analyst signs in and receives a random opaque bearer token. Only its digest
   is stored and the session expires after a bounded interval.
3. Overview and event queries derive organization scope from that session.
4. Search and severity filters return bounded, paginated results.
5. CSV, JSON, or JSONL is read up to the configured byte limit, normalized, and
   previewed without persistence.
6. A distinct confirmation request imports the same validated format.

## Security properties

- Development service ports remain bound to localhost.
- Default demo credentials are explicitly development-only.
- No uploaded content is evaluated or executed.
- UTF-8, file extension, record count, size, field length, severity, confidence,
  and timezone requirements fail closed.
- Raw payloads remain database evidence and are excluded from normal API lists
  and operational logs.
- Tenant-owned event reads and writes use the authenticated organization ID.

## Final validation results

- Backend formatting, lint, strict typing, and 21 tests passed with 96.05% coverage.
- Frontend formatting, lint, strict typing, and 4 interaction tests passed with
  94.28% statement, 87.03% branch, 86.11% function, and 96.77% line coverage.
- The frontend production build completed successfully.
- Docker rebuilt both application images; PostgreSQL, Redis, and the backend
  reported healthy, and the frontend started successfully.
- Browser validation confirmed local login, 36 seeded events, event detail,
  pagination, severity filtering, responsive sign-out, and no console errors.
- The safe preview/import boundary is covered by frontend interaction tests and
  backend parser, size, record-count, validation, and persistence tests.
