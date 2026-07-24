# Phase 3 validation

## Scope

Phase 3 introduces a common vulnerability-finding record and accountable
investigation workflow. Findings remain distinct from alerts and confirmed
incidents. Investigations link existing evidence instead of copying or altering
it, and material analyst actions create append-only audit records.

## Required gate

1. Migration from `0002_phase_2` to `0003_phase_3` preserves existing events and alerts.
2. Findings are uniquely refreshed by organization, source, and external identifier.
3. Imported records enforce bounded text, CVSS, timestamps, count, and evidence size.
4. Scanner-provided text and evidence are treated as data and are never executed.
5. Finding, investigation, owner, comment, link, and audit access is organization-scoped.
6. Investigations can link alerts, events, and findings only when evidence is tenant-owned.
7. Duplicate evidence links fail closed.
8. Accepted-risk findings require an exception reason.
9. Resolved investigations require an explicit resolution record.
10. Status, ownership, evidence-link, comment, and resolution actions remain auditable.
11. Existing Phase 2 ingestion and alert behavior remains intact.
12. Formatting, lint, types, tests, coverage, builds, migration, and Docker health pass.

## Synthetic walkthrough

The development seed creates one synthetic high-severity vulnerability finding
for `lab-web-01` and one investigation linked to it. In the workspace:

1. Open **Vulnerability findings** and inspect the affected asset and guidance.
2. Open **Investigations**, select **Review lab web exposure**, and inspect the
   linked record, analyst note, and audit history.
3. Add a note, move the case to **in progress**, then enter a synthetic resolution.
4. Resolve the case and confirm that its linked evidence remains present.

## Honest limitations

- Findings are imported from established scanners; Avenward does not scan or exploit hosts.
- Only JSON API import is implemented in this phase; vendor adapters remain roadmap work.
- Asset identity is a bounded scanner-supplied identifier, not yet a full asset inventory.
- Audit records are application-enforced and append-only through the public API; database
  administrator tamper-evidence and external audit export remain future hardening work.
- There is no automatic containment, patch deployment, or remediation execution.
