# Known limitations

Version `0.0.1` is a development foundation, not a usable monitoring product.

## Product limitations

- No authentication, organizations, roles, or authorization
- No application database schema or migrations
- No event ingestion, normalization, storage, or search
- No detection rules, alerts, incidents, assets, or metrics
- No anomaly models, AI explanations, reports, or notifications
- No collector, syslog, SNMP, Windows agent, or Linux agent

## Security limitations

- No independent security review or penetration test
- No TLS termination, production secrets workflow, CSP, rate limiting, or WAF
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
- Browser end-to-end tests begin when the authenticated demo workflow exists

Each limitation maps to a release item in the development roadmap.
