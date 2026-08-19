# Database Source Configuration Specification Delta

## Added Requirements

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
