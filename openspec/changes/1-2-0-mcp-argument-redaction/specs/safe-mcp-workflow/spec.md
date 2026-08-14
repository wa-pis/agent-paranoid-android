# Safe MCP Workflow Specification Delta

## ADDED Requirements

### Requirement: Rejected MCP Arguments Are Not Reflected

Generator and Trino MCP transports SHALL replace typed argument-validation
failures with a fixed local error before returning a tool result.

#### Scenario: A typed tool argument is rejected

- **GIVEN** a caller supplies a bounded value that fails FastMCP/Pydantic
  argument validation
- **WHEN** either MCP server dispatches the tool call
- **THEN** the tool is not executed
- **AND** the response contains the fixed `Tool arguments failed validation`
  error
- **AND** the rejected value and nested validation exception are not returned
