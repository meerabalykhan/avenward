# Development roadmap

Each phase ends with tests, formatting, linting, type checks, documentation,
recorded limitations, a descriptive commit, and explicit approval to continue.

## `0.0.1` — foundation

Repository, backend health surface, frontend shell, PostgreSQL, Redis, Nginx,
Docker Compose, CI, core documentation, security baseline, and community files.

**Gate:** clean Docker configuration; backend and frontend checks and builds;
honest readiness behavior; no secrets.

## `0.1.0` — event explorer

- Authentication and safe session lifecycle
- Organizations, members, and environments
- Alembic migrations and tenant-scoped persistence
- Generic CSV, JSON, and JSONL ingestion preview
- Canonical normalized events and paginated search
- Deterministic synthetic data generator
- Overview dashboard and event detail

**Gate:** complete login-to-search workflow, organization-isolation tests, upload
limits, parser tests, and reproducible demo.

## `0.2.0` — detections and alerts

Declarative rule schema; selected authentication and NOC rules; rule tests;
alert evidence, deduplication, state, list, and detail experiences.

## `0.3.0` — investigations

Incidents, linked alerts, comments, ownership, timelines, resolution, and audit
history without automatic containment or remediation.

## `0.4.0` — NOC monitoring

Assets, synthetic metric ingestion, time series for CPU, memory, disk, latency,
and availability, plus threshold and offline alerts.

## `0.5.0` — anomaly analysis

Rolling robust baselines and carefully justified Isolation Forest models;
organization-isolated training; versioned features and model cards; deterministic
tests; explanation features; synthetic evaluation labels.

## `0.6.0` — grounded explanations

Disabled and template providers, alert explanations, incident summaries,
citations to internal records, secret redaction, prompt-injection tests, and an
optional external-provider interface disabled by default.

## `0.7.0` — reports and notifications

HTML/PDF reports, structured exports, email and generic webhook providers,
rate limits, retries, deduplication, and delivery records.

## `0.8.0` — hardening

Threat-model review, authorization review, file-upload hardening, rate limits,
security test suite, dependency/secret/container scanning, and VM guidance.

## `0.9.0` — release candidate

Setup wizard, backup and tested restore, upgrades and rollback, accessibility
review, reproducible performance benchmark, complete demo, and documentation audit.

## `1.0.0` — first public release

Only after all required checks pass, no critical defect remains, independent
clean installation succeeds, license review completes, limitations are explicit,
and release/security checklists are signed off.

## Approval boundaries

Explicit approval is required before changing the main stack or license, adding a
paid dependency or telemetry, enabling external AI, using workplace data,
deploying publicly, adding remediation, changing Git history, or publishing.
