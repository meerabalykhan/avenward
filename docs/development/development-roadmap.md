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
alert evidence, deduplication, state, list, and detail experiences. Add the first
bounded real-ingestion paths: authenticated webhook ingestion and a documented
syslog gateway/forwarder path. Ingestion is queued, observable, retry-bounded,
tenant-scoped, and protected by size, rate, and retention limits.

**Gate:** synthetic and real-ingestion fixtures produce the same canonical
events; malformed or hostile records remain inert; rules are deterministic;
alerts retain the evidence and rule version that created them.

## `0.3.0` — investigations

Incidents, linked alerts, comments, ownership, timelines, resolution, and audit
history without automatic containment or remediation. Introduce a common
finding model for imported vulnerability results, affected assets, severity,
evidence, remediation guidance, exceptions, and resolution state. Initially
ingest results from established scanners rather than implementing a new network
exploitation engine.

**Gate:** findings and incidents remain organization-scoped, every material
change is auditable, and imported scanner content is treated as untrusted data.

## `0.4.0` — NOC monitoring

Assets, synthetic metric ingestion, time series for CPU, memory, disk, latency,
and availability, plus threshold and offline alerts. Add a signed,
least-privileged endpoint collector prototype for Windows and Linux telemetry,
with explicit enrollment, revocation, buffering, health, and uninstall
behavior. Support inventory and security posture visibility without claiming
native antivirus prevention. Define adapters for endpoint-protection products
and network devices so their alerts and state can appear in Avenward.

**Gate:** collector threat model and protocol tests pass; collection is opt-in,
resource-bounded, removable, and unable to execute server-supplied arbitrary
commands.

## `0.5.0` — anomaly analysis

Rolling robust baselines and carefully justified Isolation Forest models;
organization-isolated training; versioned features and model cards; deterministic
tests; explanation features; synthetic evaluation labels. Correlate anomalies
with asset inventory and vulnerability findings to create explainable exposure
priorities, while keeping anomaly, vulnerability, and confirmed compromise as
distinct states.

## `0.6.0` — grounded explanations

Disabled and template providers, alert explanations, incident summaries,
citations to internal records, secret redaction, prompt-injection tests, and an
optional external-provider interface disabled by default.

## `0.7.0` — reports and notifications

HTML/PDF reports, structured exports, email and generic webhook providers,
rate limits, retries, deduplication, and delivery records. Add response
playbooks that default to recommendation-only mode. A small allowlist of
reversible actions may be executed through separately configured adapters only
after an authorized human reviews the evidence and approves the exact action.
Every request, approval, execution, result, and rollback is audited.

No autonomous containment, destructive action, or arbitrary remote shell is a
`1.0.0` requirement.

## `0.8.0` — hardening

Threat-model review, authorization review, file-upload hardening, rate limits,
security test suite, dependency/secret/container scanning, and VM guidance.
Complete production identity basics: invitations, password recovery, MFA,
role-based access, session administration, and an SSO integration boundary.
Harden the collector and integration credential lifecycle. Validate adapters
for at least one endpoint-protection source, one firewall/network source, and
one vulnerability-scanner source without pretending Avenward replaces their
packet, malware, or scanning engines.

## `0.9.0` — release candidate

Setup wizard, backup and tested restore, upgrades and rollback, accessibility
review, reproducible performance benchmark, complete demo, and documentation
audit. Add retention/storage administration, integration health, customer-safe
diagnostics, and an MSP-ready tenancy review covering delegated administration
and strict customer isolation. Produce deployment and operational runbooks for
a supported single-node installation.

Billing automation, contractual SLAs, and a staffed 24/7 managed service are
business operations and are not release-gate substitutes for product safety.

## `1.0.0` — first public release

Only after all required checks pass, no critical defect remains, independent
clean installation succeeds, license review completes, limitations are explicit,
and release/security checklists are signed off. The release is positioned as a
self-hosted defensive operations and integration platform for lean teams and
service providers. It may centralize endpoint, firewall, vulnerability, event,
and operational evidence; it does not claim feature parity with every specialist
engine or replacement of experienced analysts.

## Capability interpretation for `1.0.0`

| Ambition | `1.0.0` interpretation |
| --- | --- |
| Antivirus / endpoint protection | Endpoint visibility plus integrations with established protection engines; a new native malware-prevention engine is post-1.0 research. |
| Firewall | Ingest firewall evidence and support narrowly allowlisted, human-approved adapter actions; Avenward is not a packet-processing firewall. |
| Vulnerability scanner | Normalize and manage findings from established scanners; safe native inventory checks may be added, but exploit-based scanning is not required. |
| Penetration testing | Store authorized assessment evidence and reports; no built-in exploitation framework in 1.0. |
| Offensive hacking | Explicitly outside the product. Avenward remains defensive and authorized-use only. |
| 24/7 managed security | Make the product usable by MSSPs; staffing a round-the-clock service is a separate company offering requiring people, procedures, contracts, and insurance. |
| Automatic remediation | Recommendation-first and human-approved reversible playbooks only. |
| Analyst replacement | Analyst assistance, prioritization, and explanation; accountable decisions remain human. |
| Splunk/CrowdStrike/Palo Alto replacement | A focused alternative for lean self-hosted operations, with integrations where specialist controls remain stronger; no universal parity claim. |
| Production readiness | Supported only for the documented deployment after hardening, independent installation, recovery, and security gates pass. |

This scope is substantially larger than the original roadmap. Schedule and
release claims must be re-estimated after design spikes for collectors,
production identity, integrations, and response adapters; quality gates must not
be weakened to preserve an earlier date.

## Approval boundaries

Explicit approval is required before changing the main stack or license, adding a
paid dependency or telemetry, enabling external AI, using workplace data,
deploying publicly, adding remediation, changing Git history, or publishing.
