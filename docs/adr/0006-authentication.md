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
session management.

## Current implementation note

Version `0.3.0` does not implement the proposed production design above. Its
localhost-only demonstration authentication uses salted `scrypt` password
hashes, random opaque bearer tokens, database-stored SHA-256 token digests,
expiry, and explicit revocation. The browser keeps the demonstration token in
session storage. This is intentionally narrower than the proposed Argon2id and
HTTP-only refresh-cookie design and must not be treated as production identity.
