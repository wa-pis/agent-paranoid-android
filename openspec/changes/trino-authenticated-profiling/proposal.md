# Change Proposal: trino-authenticated-profiling

## Summary
Verify the existing authenticated Trino connection routes for aggregate-only
profiling and MCP, then reconcile the external failure against version and
configuration evidence. Implement only independently reproduced gaps.

## Motivation
External O/#21 reports an authentication failure. Current main already exposes
`TrinoAuthConfig` and runtime secret references, including basic, JWT, certificate,
Kerberos/GSSAPI and explicit OAuth2. The historical failure does not establish
that authentication is absent in current main.

## Scope
P1 verification: enumerate connection factories, rerun typed authentication and
TLS validation, fake-driver and sanitized failure tests. Compare documented
configuration with external evidence before proposing any runtime change.

Out of scope: new secret-store integrations, logging secrets, JDBC credentials,
disabling TLS, arbitrary SQL, real server access or automatic credential discovery.

## Safety Impact
Secrets must be excluded from repr, serialization, fingerprints, audit evidence,
exceptions and MCP/CLI/provider payloads. Validate before connecting. Authentication
does not expand table/column allowlists, query budgets or source-row permissions.

## Compatibility
Preserve existing explicitly unauthenticated trusted-local usage. New auth modes
are opt-in; malformed/incomplete settings fail closed with fixed recovery text.
Transport/security behavior changes require candidate checks and documentation.
