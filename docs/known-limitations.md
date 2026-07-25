# Known limitations

## Version 0.3.0

- Authentication is a local demonstration identity, not production SSO, MFA,
  recovery, invitation, or account administration.
- The example password is intentionally public and the stack must stay on
  localhost. Change `.env` values before any extended local evaluation.
- Interactive file import runs within the API request and is limited to 2 MB /
  5,000 records. Authenticated webhook ingestion uses a background worker, but
  throughput and failure recovery have not been benchmarked.
- Search uses bounded relational matching, not a dedicated search engine.
- The demo generator is deterministic but its timestamps are based on seed time.
- Detection rules are a small, versioned, declarative demonstration set rather
  than a complete detection library.
- Alerts, vulnerability findings, and investigations use synthetic evidence and
  are not proof of compromise or production monitoring.
- The audit history is append-only through the application workflow, but it is
  not cryptographically tamper-evident or an independently reviewed compliance
  ledger.
- No anomaly models or AI explanations exist yet. Confidence is supplied
  evidence metadata, not an AI score.

Version `0.3.0` is a local development prototype, not a usable monitoring or
incident-response product.

## Product limitations

- No production SSO, MFA, recovery, invitations, or role administration
- No native vulnerability scanner, endpoint agent, prevention, or remediation
- No anomaly models, AI explanations, reports, or notifications
- No collector, syslog, SNMP, Windows agent, or Linux agent

## Security limitations

- No independent security review or penetration test
- A restrictive development CSP is present, but there is no TLS termination,
  production secrets workflow, rate limiting, or WAF
- Development credentials in `.env.example` are intentionally non-secret and
  must never be reused for a deployment
- No public-internet deployment is supported
- No real, workplace, customer, or personal data is permitted

## Operational limitations

- Local Docker Compose is the only documented deployment target
- Backup, restore, upgrade, rollback, retention, and log rotation are not yet
  implemented
- Performance and resource consumption have not been benchmarked
- PostgreSQL and Redis are single local containers without high availability

## Validation limitations

- Docker validation depends on the Docker CLI being accessible to the execution
  environment; any unavailable check is reported in the Phase 0 handoff
- Frontend workflow tests run in a simulated browser environment; no independent
  cross-browser or production end-to-end test suite exists

Each limitation maps to a release item in the development roadmap.
