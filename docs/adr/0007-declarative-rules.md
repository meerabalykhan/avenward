# ADR 0007: Detection rules are declarative data

- Status: Accepted
- Date: 2026-07-23

## Decision

Rules use a versioned, allowlisted YAML or JSON schema containing filters,
grouping, thresholds, windows, severity, and evidence templates. Rule definitions
cannot contain Python, shell, templates with executable expressions, or arbitrary
database queries.

## Consequences

Rules are reviewable, testable, and safer for community contribution, but less
flexible than arbitrary code. New operators require explicit implementation and
security tests.
