# MCP Interface Specification Delta

## ADDED Requirements

### Requirement: MCP Discovery Schemas Are Stable

Generator and Trino MCP servers SHALL maintain reviewed contracts for default
tool names and input/output schemas.

#### Scenario: A tool schema changes

- **GIVEN** checked-in MCP discovery fixtures
- **WHEN** a tool name, input schema, or output schema changes
- **THEN** contract verification fails until compatibility is reviewed
- **AND** unrestricted raw SQL remains absent from the default Trino tools
