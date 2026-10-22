## ADDED Requirements

### Requirement: Explicit TLS-Protected Trino Authentication

Trino authentication SHALL be explicit, validated before access and independent
of query authorization. Secrets SHALL remain confined to the connection adapter.

#### Scenario: Basic authentication is selected
- **GIVEN** complete locally supplied credentials and verified HTTPS
- **WHEN** the connection adapter creates a client
- **THEN** it injects the selected driver authentication object
- **AND** all existing allowlists and work budgets still apply

#### Scenario: Credentials would be sent over HTTP
- **WHEN** basic authentication is configured with an insecure transport override
- **THEN** configuration is rejected before connection
- **AND** no credential is reflected in the error

#### Scenario: The server rejects authentication
- **WHEN** a known typed unauthorized failure is received
- **THEN** callers receive a fixed authentication failure category
- **AND** driver messages and original secret-bearing exception context are not exposed

#### Scenario: Untyped driver or TLS failure during query profiling
- **WHEN** the driver raises an untyped HTTP 401/403 or TLS failure during connection, execution or fetch
- **THEN** SQL-query profiling raises its fixed profile error without an original cause or context
- **AND** CLI JSON retains the external-service error category and any existing output artifact
- **AND** audited MCP errors and logs contain no driver message or credentials
