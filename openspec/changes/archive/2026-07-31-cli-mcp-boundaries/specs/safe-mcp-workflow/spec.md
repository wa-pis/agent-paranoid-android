# Safe MCP Workflow Specification Delta

## ADDED Requirements

### Requirement: MCP Transport Cannot Bypass Application Safety

Generator and Trino MCP transports SHALL delegate to application services that
enforce the same validation and safety policy when called directly.

#### Scenario: MCP registration is separated from a service

- **GIVEN** an existing public MCP tool and its golden contract fixture
- **WHEN** transport registration delegates to an extracted application
  service
- **THEN** the tool name, input schema, result schema, and typed errors remain
  compatible
- **AND** workspace limits, row-free responses, audit behavior, and Trino
  allowlists remain enforced
- **AND** direct service calls cannot bypass the safety checks
