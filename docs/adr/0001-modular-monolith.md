# ADR 0001: Start as a modular monolith

- Status: Accepted
- Date: 2026-07-23

## Context

The product spans many domains, but its initial team, traffic, and operating scale
do not justify distributed services.

## Decision

Use one FastAPI deployable with explicit internal module boundaries. A separate
worker may run the same codebase for asynchronous tasks.

## Consequences

Development, transactions, testing, and local installation remain understandable.
Modules must avoid circular imports and direct cross-domain persistence. Selected
boundaries may later become services only after measurements justify the cost.
