# Phase 2 validation

## Scope

Phase 2 adds a bounded real-ingestion foundation, versioned declarative rules,
deterministic evaluation, evidence-preserving alert deduplication, alert state,
and analyst-facing rule and alert views.

## Supported ingestion path

`POST /api/v1/ingestion/webhook` accepts JSON with an `events` array and requires
`X-Avenward-Ingest-Key`. The development key comes from
`AVENWARD_DEMO_INGEST_KEY`. A request is limited to 500 records, becomes a
database-backed job, and returns `202` before parsing. The worker normalizes the
records as inert data, persists them under the source organization, and evaluates
enabled rules. Failed jobs expose a bounded error code rather than payload data.

Example for the local synthetic environment:

```powershell
$headers = @{ "X-Avenward-Ingest-Key" = "avenward-demo-ingest-key" }
$body = @{ events = @(
  @{ source="identity"; category="authentication"; severity="high";
     title="Authentication failure"; actor="demo-user"; target="portal";
     observed_at=(Get-Date).ToUniversalTime().ToString("o"); confidence=90 },
  @{ source="identity"; category="authentication"; severity="high";
     title="Authentication failure"; actor="demo-user"; target="portal";
     observed_at=(Get-Date).ToUniversalTime().ToString("o"); confidence=90 },
  @{ source="identity"; category="authentication"; severity="high";
     title="Authentication failure"; actor="demo-user"; target="portal";
     observed_at=(Get-Date).ToUniversalTime().ToString("o"); confidence=90 }
) } | ConvertTo-Json -Depth 4
Invoke-RestMethod http://localhost:8000/api/v1/ingestion/webhook `
  -Method Post -Headers $headers -ContentType "application/json" -Body $body
```

Refresh the application after the worker completes. One deduplicated alert must
show three evidence events for `demo-user`.

## Syslog gateway boundary

Phase 2 does not expose an unauthenticated UDP listener. A syslog gateway such as
Vector, Fluent Bit, or rsyslog must terminate syslog, map records to the documented
canonical JSON fields, and call the authenticated webhook over a protected local
or private network. Production TLS and credential lifecycle are Phase 8 work.

## Required gate

1. Migration upgrade from `0001_phase_1` to `0002_phase_2` succeeds.
2. Existing Phase 1 events remain intact.
3. Missing or invalid ingestion keys return `401` without revealing source data.
4. Oversized or malformed batches fail closed.
5. Rule definitions accept only bounded fields and operators; no code is executed.
6. Rule and alert queries remain scoped by `organization_id`.
7. Threshold rules create one deduplicated alert per explicit time bucket.
8. Alert evidence retains event IDs and the creating rule version.
9. Open, acknowledged, and resolved state changes do not alter evidence.
10. Backend and frontend formatting, lint, types, tests, coverage, and builds pass.
11. Docker services, including the worker, start successfully and report healthy.

## Honest limitations

- Only the seeded authentication-failure and offline rules are provided.
- The webhook is the only implemented real-ingestion API.
- The database job queue is intentionally simple and not a high-volume broker.
- Rule conditions support canonical string equality and containment only.
- Alerts use fixed windows rather than streaming event-time watermarks.
- No endpoint collector, firewall integration, vulnerability scanner, incident,
  anomaly model, AI explanation, or response action exists yet.
