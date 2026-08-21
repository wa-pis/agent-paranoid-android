# Database Source Configuration Specification

## Purpose

Define safe additive endpoint configuration for PostgreSQL and Trino sources.

## Requirements

### Requirement: JDBC-Style Endpoint Input

The application SHALL accept documented PostgreSQL and Trino JDBC-style URLs
as additive endpoint input and SHALL normalize them into the existing typed
Python adapter configuration without loading Java or a JDBC driver.

#### Scenario: PostgreSQL endpoint is valid

- **GIVEN** a PostgreSQL JDBC-style URL with a host, port, database, and an
  allowed TLS property
- **WHEN** database configuration is validated
- **THEN** the endpoint is normalized into `PostgresConfig`
- **AND** existing read-only, allowlist, and resource-budget policy remains in
  force

#### Scenario: Trino endpoint is valid

- **GIVEN** a Trino JDBC-style URL with a host, port, optional catalog/schema,
  and verified TLS enabled
- **WHEN** database configuration is validated
- **THEN** the endpoint is normalized into `TrinoConfig` and validated Trino
  request defaults
- **AND** the existing Python Trino client remains the runtime adapter

### Requirement: URL Secrets And Session Properties Are Forbidden

JDBC-style URL input SHALL reject credentials, tokens, secrets, userinfo,
proxies, arbitrary headers, session properties, SQL paths, roles,
initialization behavior, TLS verification downgrades, and unknown properties.

#### Scenario: URL contains a credential

- **GIVEN** a JDBC-style URL containing a password, access token, extra
  credential, or other secret-bearing property
- **WHEN** configuration is validated
- **THEN** validation fails before network access
- **AND** the URL and property value are absent from logs, errors, profiles,
  MCP responses, provider payloads, and artifacts

#### Scenario: URL conflicts with component configuration

- **GIVEN** a JDBC-style URL and explicit component configuration that disagree
- **WHEN** configuration is validated
- **THEN** validation fails before client construction
- **AND** neither value is disclosed in the error

### Requirement: JDBC-Style Endpoint Input Is Resource-Bounded

JDBC-style URL parsing SHALL enforce finite URL and component limits before
client construction and SHALL reject oversized input with a fixed error that
does not include the rejected value.

#### Scenario: URL or component exceeds its limit

- **GIVEN** a JDBC-style URL whose UTF-8 bytes, host, database, catalog, or
  schema exceed the documented adapter limit
- **WHEN** configuration is validated
- **THEN** validation fails before network access
- **AND** the URL and oversized component are absent from the error

### Requirement: Runnable JDBC Source Examples

The repository SHALL provide separate PostgreSQL and Trino JDBC launchers that
reuse disposable synthetic services and exercise the installed public package
through safe profiling and deterministic generation.

#### Scenario: PostgreSQL JDBC example runs

- **GIVEN** an installed package with the `postgres` extra and local PostgreSQL
  test tools
- **WHEN** `examples/local_postgres/run-jdbc.sh` runs with a new output path
- **THEN** it uses a placeholder JDBC-style endpoint and mandatory exact
  allowlists to profile, infer, generate, validate, and export SQL
- **AND** artifacts report synthetic output with no copied source rows

#### Scenario: Trino JDBC example runs

- **GIVEN** an installed package with the `trino` extra and the existing pinned
  disposable Trino service
- **WHEN** `examples/local_trino/run-jdbc.sh` runs with a new output path
- **THEN** it uses a placeholder JDBC-style endpoint and mandatory allowlists
  to build a safe aggregate profile and deterministic generated output
- **AND** no JDBC URL, credential, endpoint, or source row appears in artifacts
