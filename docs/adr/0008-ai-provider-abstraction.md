# ADR 0008: Put AI behind a provider abstraction

- Status: Accepted
- Date: 2026-07-23

## Decision

Support disabled, deterministic template, local-model, and external-LLM provider
interfaces. Core detection never depends on an LLM. Factual answers about tenant
data require retrieved evidence references.

## Consequences

Avenward remains useful offline and avoids vendor lock-in. External providers add
privacy, cost, prompt-injection, and reliability risks and therefore require
administrator enablement, redaction, minimization, auditing, and optional
per-request confirmation.
