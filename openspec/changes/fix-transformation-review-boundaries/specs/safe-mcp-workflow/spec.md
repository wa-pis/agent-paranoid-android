## ADDED Requirements

### Requirement: Transformation stages retain the shared request deadline
MCP single and common transformation consumers SHALL enforce the active shared
request invocation deadline at their existing work checkpoints, including the
last checkpoint before publication and the checkpoint after rename/fsync. The generation deadline and byte ceilings
SHALL also apply. Expiry SHALL stop work without a new retained publication and
return a typed value-free invocation deadline error.

#### Scenario: Deadline expires during capture or execution
- **GIVEN** an admitted MCP request and fictional bound local input
- **WHEN** its shared deadline expires during transformation work
- **THEN** review, validation or execution rejects at the next checkpoint
- **AND** original artifacts remain intact and no retained destination is published.

#### Scenario: Deadline expires before directory rename
- **WHEN** the request deadline expires while staging the validated bundle
- **THEN** the pre-publication checkpoint rejects and removes only owned staging
- **AND** unverifiable cleanup keeps its distinct cleanup-incomplete error.

#### Scenario: Legitimate caller has no shared MCP context
- **WHEN** direct local execution runs without an active MCP request budget
- **THEN** the existing generation and byte ceilings apply without inventing
  a new MCP timeout or changing local receipt authority.

#### Scenario: Deadline expires during directory publication
- **WHEN** the shared deadline expires during rename or directory fsync
- **THEN** the completion checkpoint rejects within the cleanup-protected block
- **AND** identity-confirmed retained output is removed before returning the error.
