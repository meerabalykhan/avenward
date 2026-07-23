# Avenward product requirements

## Document status

- Product: Avenward
- Version: `0.1.0`
- Status: implemented local event explorer scope
- Updated: 2026-07-23

## Vision

Avenward gives small organizations and learners a calm, understandable place to
collect, normalize, search, and interpret authorized security and operational
data. It combines foundational SOC and NOC workflows without claiming to replace
an enterprise SIEM or an experienced analyst.

## Users and jobs

Primary users are junior SOC and NOC analysts, system and network administrators,
small IT teams, educators, students, NGOs, startups, and authorized laboratories.
They need to:

1. Import logs and metrics safely.
2. Convert different records into one understandable event format.
3. Search evidence and recognize meaningful changes.
4. Create, investigate, and resolve alerts and incidents.
5. Understand findings without overstating certainty.
6. Produce reports and controlled notifications.

## Product principles

- Defensive and advisory, never autonomously offensive or destructive
- Useful when external AI is disabled
- Self-hosted and privacy-conscious
- Secure defaults and explicit trust boundaries
- Evidence and uncertainty shown together
- Modular monolith until measured scale requires otherwise
- Synthetic data for development and demonstrations
- Accessible language and interface for junior analysts

## Foundation scope (`0.0.1`)

The foundation must provide:

- A versioned repository with community and licensing files
- FastAPI application with `/api/v1/health`, `/api/v1/ready`, and
  `/api/v1/version`
- Readiness checks that reflect PostgreSQL and Redis availability
- React and TypeScript landing shell with honest pre-release labeling
- PostgreSQL and Redis Docker services
- Nginx entry point for the frontend
- Tests and CI checks for both application layers
- Product, architecture, threat, roadmap, limitations, and decision records

## Explicitly out of scope for `0.0.1`

- Authentication or user data
- Event ingestion, normalization, or search
- Detection rules, alerts, or incidents
- Asset monitoring or metric collection
- Machine-learning models
- AI-generated explanations
- Notifications, reports, billing, telemetry, or public deployment

## Functional roadmap summary

The first useful vertical slice in `0.1.0` will support an account, one
organization, synthetic CSV/JSON import, normalized event storage, event search,
event detail, and a basic overview dashboard. Later releases add detections,
incidents, metrics, anomaly analysis, grounded explanations, and reports.

## Non-functional requirements

- Organization-owned queries must be scoped by `organization_id`.
- Time values must be timezone-aware and stored in UTC.
- Inputs must be typed and validated.
- Uploaded data must never be executed.
- Operational logs must not contain secrets or raw event payloads.
- User-facing lists must be paginated before realistic volume testing.
- External network transmission requires explicit administrator enablement.
- Heavy ingestion and model training must not block API workers.

## Foundation acceptance criteria

1. Docker Compose configuration resolves successfully.
2. Backend formatting, lint, type checking, and unit tests pass.
3. Frontend formatting, lint, type checking, tests, and production build pass.
4. Health returns success without dependencies; readiness reports dependency
   state and fails closed if required services are unavailable.
5. No credentials or real operational data are committed.
6. Setup and limitations are documented honestly.

## Success measures for later validation

The MVP will be evaluated by installation success, time to first imported event,
search latency on documented synthetic datasets, detection false-positive rate,
alert volume, task completion, accessibility checks, and user comprehension.
No scale or accuracy claim will be made without a reproducible benchmark.

## Event explorer scope (`0.1.0`)

The first usable vertical slice provides a development-only account and one
organization, revocable opaque sessions, organization-scoped persistence,
generic file preview/import, deterministic synthetic evidence, normalized event
search, overview counts, and event detail. Uploads are bounded to 2 MB and 5,000
records, require UTF-8 CSV/JSON/JSONL, and are parsed strictly as inert data.
