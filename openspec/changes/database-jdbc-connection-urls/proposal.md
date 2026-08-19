# Change Proposal: database-jdbc-connection-urls

## Summary

Accept PostgreSQL and Trino JDBC-style connection URLs as an additive,
human-friendly way to configure the existing Python database adapters. The
application parses the URL into the current typed connection models; it does
not load a JVM or JDBC driver.

## Motivation

Many teams already receive database endpoints in JDBC form from platform
portals and secret-management workflows. Requiring users to split the same
endpoint into several environment variables adds avoidable setup work and
makes copy errors more likely.

## Scope

In scope:

- PostgreSQL URLs in the documented `jdbc:postgresql://host:port/database`
  family.
- Trino URLs in the documented
  `jdbc:trino://host:port/catalog/schema` family.
- Additive typed configuration and CLI/environment inputs that normalize into
  the existing `PostgresConfig`, `TrinoConfig`, and Trino request-default
  boundaries.
- A small per-adapter allowlist of safe transport properties, including
  verified TLS selection.
- Deterministic precedence and fail-closed conflict handling when URL and
  component settings are both supplied.
- Redacted validation, diagnostics, and tests using placeholder endpoints.
- Runnable PostgreSQL and Trino examples that reuse the existing disposable
  synthetic services and complete the normal profile-to-generation workflow.

Out of scope:

- Java, a JVM, JDBC JARs, or replacing the existing `psycopg` and `trino`
  Python clients.
- Credentials, tokens, secrets, proxy configuration, session properties,
  arbitrary headers, SQL paths, roles, or initialization SQL inside a URL.
- General JDBC support or additional database engines.
- Changing schema, table, or column authorization, query policy, profiling,
  generation, or artifact contracts.

## Safety Impact

The URL is untrusted local configuration. Parsing happens before connection
creation, accepts only the expected adapter scheme and bounded components, and
rejects userinfo, fragments, duplicate parameters, unknown properties, and
credential-bearing properties. Authentication continues to use existing
runtime secret indirection.

The complete URL is secret-adjacent and must not appear in profiles, manifests,
logs, exceptions, MCP responses, provider requests, or generated artifacts.
Connection behavior remains read-only, allowlisted, and resource-bounded after
normalization.

## Compatibility

Existing component environment variables and Python constructors remain
supported. JDBC URL support is additive. Supplying both forms with conflicting
explicit values fails before network access rather than selecting one
silently. The base package gains no Java or database dependency.

The existing component-based examples remain the default baseline. JDBC
launchers are additive and must not require real credentials or production
infrastructure.

## Release Impact

Implementation adds public configuration and CLI behavior and therefore
requires a future minor release candidate. This proposal does not change the
package version, create a tag, or publish artifacts.
