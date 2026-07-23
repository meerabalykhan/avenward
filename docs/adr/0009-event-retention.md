# ADR 0009: Use bounded event retention

- Status: Proposed
- Date: 2026-07-23

## Proposed decision

Default raw payload retention will be short and independently configurable from
normalized events. Deletion must be observable and respect incident/report holds.

## Open questions

Exact defaults require measurements of storage growth, user needs, export and
legal obligations. Before ingestion ships, document deletion jobs, backup
interaction, administrator controls, and development-safe defaults.
