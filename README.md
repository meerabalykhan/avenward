# Avenward

**Clarity across security and operations.**

Avenward is an early-stage, self-hosted platform for collecting, normalizing,
searching, and interpreting security and operational data. It is designed for
small teams, students, and authorized laboratories that need an understandable
foundation for SOC and NOC workflows without an enterprise platform.

> **Status:** `0.3.0` investigation workspace under active development. Avenward is not
> production-ready and must not
> be exposed to the public internet.

## What exists today

- FastAPI backend with health, readiness, and version endpoints
- Local demo authentication with revocable opaque sessions
- Organization-scoped PostgreSQL persistence and Alembic migrations
- Safe CSV, JSON, and JSONL preview/import (2 MB and 5,000-event limits)
- Canonical event search, overview, detail, and deterministic synthetic data
- Database-backed authenticated webhook ingestion worker
- Versioned declarative authentication and availability rules
- Evidence-preserving alert creation, deduplication, state, list, and rationale views
- Imported vulnerability findings with affected assets and remediation guidance
- Investigations with linked evidence, ownership, notes, resolution, and audit history
- React and TypeScript analyst workspace
- PostgreSQL and Redis development services
- Docker Compose development workflow
- Backend and frontend tests, linting, formatting, and type checks
- Product, architecture, security, roadmap, limitation, and decision documents

Additional rules, endpoint collectors, native scanning, security-control integrations,
response playbooks, and AI-assisted analysis are roadmap work and are not represented
as complete.

All bundled records and screenshots are synthetic demonstrations. The current
audit history is append-only through application workflows; it is not a
tamper-evident compliance ledger.

## Quick start

Requirements: Git, Docker Desktop with WSL 2, and Docker Compose.

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open:

- Application: <http://localhost:8080>
- Backend API documentation: <http://localhost:8000/docs>
- Backend health: <http://localhost:8000/api/v1/health>

The local demonstration account is configured in `.env`. The example values are
`analyst@example.com` and `avenward-demo-only`; change them before importing
anything beyond the deterministic synthetic demo. Previewing does not persist a
file. Only **Confirm import** writes validated, normalized events.

Stop the stack with `docker compose down`. The PostgreSQL data is retained in a
named volume. Use `docker compose down --volumes` only when intentionally
discarding local development data.

## Local development

The Docker workflow is the supported beginner path. These helpers run checks in
temporary containers, so Python and Node.js do not need to be installed locally.

```powershell
.\scripts\windows\dev.ps1 check
.\scripts\windows\dev.ps1 test
```

See [development roadmap](docs/development/development-roadmap.md),
[system architecture](docs/architecture/system-architecture.md), and
[known limitations](docs/known-limitations.md).

## Security and data

- Use synthetic data only during development.
- Never commit `.env`, passwords, tokens, workplace logs, or customer data.
- Avenward is defensive software. The `1.0.0` roadmap permits only narrowly
  allowlisted, reversible, human-approved response actions; autonomous
  destructive remediation and offensive exploitation remain out of scope.
- Report suspected vulnerabilities using [SECURITY.md](SECURITY.md).

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## License and trademarks

Code is licensed under the Apache License 2.0. See [LICENSE](LICENSE).
The name and marks are addressed separately in [TRADEMARKS.md](TRADEMARKS.md).
Avenward is not affiliated with OpenAI, Microsoft, Splunk, IBM, Elastic, or
other vendors.
