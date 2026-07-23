# Avenward

**Clarity across security and operations.**

Avenward is an early-stage, self-hosted platform for collecting, normalizing,
searching, and interpreting security and operational data. It is designed for
small teams, students, and authorized laboratories that need an understandable
foundation for SOC and NOC workflows without an enterprise platform.

> **Status:** `0.0.1` foundation. Avenward is not production-ready and must not
> be exposed to the public internet.

## What exists today

- FastAPI backend with health, readiness, and version endpoints
- React and TypeScript landing shell
- PostgreSQL and Redis development services
- Docker Compose development workflow
- Backend and frontend tests, linting, formatting, and type checks
- Product, architecture, security, roadmap, limitation, and decision documents

Event ingestion, authentication, detection, alerts, incidents, and AI-assisted
analysis are roadmap work and are not represented as complete.

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
- Avenward is defensive software; it does not perform autonomous remediation.
- Report suspected vulnerabilities using [SECURITY.md](SECURITY.md).

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## License and trademarks

Code is licensed under the Apache License 2.0. See [LICENSE](LICENSE).
The name and marks are addressed separately in [TRADEMARKS.md](TRADEMARKS.md).
Avenward is not affiliated with OpenAI, Microsoft, Splunk, IBM, Elastic, or
other vendors.
