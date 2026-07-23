# Contributing to Avenward

Thank you for helping build a calm, evidence-led defensive monitoring platform.

## Ground rules

- Work only with synthetic or explicitly authorized, anonymized data.
- Do not add offensive capabilities, active remediation, or arbitrary code execution.
- Never commit secrets or personal, workplace, or customer data.
- Add tests and documentation with behavioral changes.
- Keep changes focused and use descriptive commits.

## Development workflow

1. Open an issue for significant behavior or architecture changes.
2. Create a branch from `main`.
3. Run `./scripts/windows/dev.ps1 check` on Windows or `make check` on Linux.
4. Update `CHANGELOG.md` for user-visible changes.
5. Open a pull request using the repository template.

Security vulnerabilities must be reported privately as described in
[SECURITY.md](SECURITY.md), not in a public issue.
