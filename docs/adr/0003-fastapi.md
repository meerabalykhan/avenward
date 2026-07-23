# ADR 0003: Use FastAPI for the backend API

- Status: Accepted
- Date: 2026-07-23

## Decision

Use Python 3.12, FastAPI, Pydantic, SQLAlchemy, and generated OpenAPI under
`/api/v1`. Keep business rules out of route handlers.

## Consequences

Typed validation and Python's data ecosystem support ingestion, reports, and
statistical analysis. Async operations require discipline: CPU-heavy and long
tasks must leave API workers.
