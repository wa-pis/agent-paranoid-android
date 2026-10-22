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
