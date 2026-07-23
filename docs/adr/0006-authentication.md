# ADR 0006: Prefer server-managed refresh sessions

- Status: Proposed
- Date: 2026-07-23

## Decision under review

Use Argon2id password hashes, short-lived in-memory access credentials, and
rotating refresh credentials held in secure, HTTP-only, same-site cookies.
Persist hashed refresh-session identifiers for revocation and audit. Do not store
long-lived bearer tokens in browser local storage.

## Required validation

Before acceptance, specify CSRF controls, cookie deployment behavior, password
reset tokens, account enumeration defenses, login throttling, and multi-device
session management. Authentication is not implemented in `0.0.1`.
