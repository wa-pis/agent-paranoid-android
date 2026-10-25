## ADDED Requirements

### Requirement: SDK-major compatibility preserves the safety boundary

The transport SHALL support the reviewed MCP 1.x and 2.x SDK range using the
same published tool schemas and bounded JSON-RPC stdio writer. Each invocation
SHALL retain its own shared work budget through SDK tool dispatch.

#### Scenario: SDK 2 dispatches a synchronous tool

- **WHEN** the SDK dispatches a tool through its worker thread
- **THEN** the tool receives its invocation context and shared budget
- **AND** context is reset after completion or failure.

#### Scenario: SDK 2 wraps an unexpected application failure

- **WHEN** an unexpected tool exception contains private values
- **THEN** the client receives a fixed error without those values
- **AND** the SDK logger does not receive the original exception chain.

#### Scenario: Public wire contract remains stable

- **WHEN** either supported SDK major serializes tool definitions or results
- **THEN** camel-case protocol aliases and golden schemas remain unchanged
- **AND** ingress and final serialized-response byte budgets still apply.
