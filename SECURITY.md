# Security Policy

Agent Paranoid Android is a safety-first synthetic data generation system. The
most important security invariant is that generated outputs must never copy
source rows, expose raw PII, or execute unrestricted SQL.

## Supported Versions

Security fixes target the current `main` branch until the project starts
publishing stable release branches. Released versions are best-effort supported
until a newer release is available.

## Reporting A Vulnerability

Please do not open public issues with secrets, raw PII, production data, or
exploit details.

Preferred reporting path:

1. Use GitHub private vulnerability reporting when it is enabled for the
   repository.
2. If private reporting is unavailable, email `onepis2word@gmail.com` with a
   concise description and reproduction steps that use synthetic data only.

Include:

- affected command, API, or MCP tool;
- expected and actual behavior;
- minimal synthetic reproduction data;
- whether generated output copied source rows or exposed sensitive values;
- any relevant logs with secrets and PII removed.

Do not include:

- production rows;
- raw emails, names, phone numbers, addresses, tokens, credentials, or secrets;
- unrestricted SQL against a real database;
- private keys, access tokens, cookies, or session data.

## Security Scope

Security-sensitive behavior includes:

- copying source rows into generated output;
- exposing raw PII in profiles, generated datasets, logs, exceptions, MCP
  responses, or cache files;
- accepting DDL, DML, unrestricted `SELECT *`, joins, CTEs, subqueries, or
  likely PII aliases in safe Trino query paths;
- path traversal or symlink escape from the configured generator workspace;
- overwriting existing artifacts without explicit approval;
- non-deterministic generation when a seed is supplied;
- validation paths that depend only on free-form LLM reasoning.
- missing or bypassable resource budgets for untrusted input, generated
  artifacts, or Trino queries.

Official GitHub Release assets include SHA-256 checksums, a CycloneDX SBOM, and
GitHub attestations. Verify those records before distributing a release build.

## Disclosure Expectations

The maintainer will acknowledge credible private reports as soon as practical,
triage severity, and publish a fix with tests before discussing details
publicly. If the issue affects users who may have generated unsafe artifacts,
release notes should include clear remediation guidance.
