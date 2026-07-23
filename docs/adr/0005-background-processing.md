# ADR 0005: Use Redis-backed background processing

- Status: Accepted
- Date: 2026-07-23

## Context

Ingestion, reports, notifications, and model training should not block API workers.

## Decision

Use Redis for queue coordination and select Celery or an equivalent Python worker
after the first asynchronous ingestion workload is implemented and compared.
Redis never becomes the durable system of record.

## Consequences

The foundation includes Redis and readiness checks but no idle worker container.
Job idempotency, retries, visibility, and dead-letter behavior must be designed
with the first job type.
