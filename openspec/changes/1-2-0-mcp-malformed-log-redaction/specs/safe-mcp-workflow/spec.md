# Safe MCP Workflow Specification Delta

## ADDED Requirements

### Requirement: Malformed MCP Values Do Not Reach SDK Logs

Generator and Trino MCP transports SHALL reject malformed typed client
messages before passing them to the MCP SDK.

#### Scenario: A typed MCP request contains a malformed value

- **GIVEN** a byte- and structure-bounded JSON-RPC request with a valid request
  ID and a caller-controlled value that fails typed MCP validation
- **WHEN** either MCP server receives the request
- **THEN** the request is not dispatched to the SDK or a tool
- **AND** the response contains code `-32602` and fixed
  `Invalid request parameters` text
- **AND** the caller-controlled value is absent from the response, local logs,
  and retained exception state

#### Scenario: A typed MCP notification contains a malformed value

- **GIVEN** a byte- and structure-bounded JSON-RPC notification that fails
  typed MCP validation
- **WHEN** either MCP server receives the notification
- **THEN** it is not dispatched to the SDK or a tool
- **AND** no response is written
- **AND** the caller-controlled value is absent from local logs and retained
  exception state
