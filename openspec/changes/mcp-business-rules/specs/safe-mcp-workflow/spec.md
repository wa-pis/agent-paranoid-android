# Safe MCP Workflow Specification Delta

## ADDED Requirements

### Requirement: Structured Business Rules

The generator MCP server SHALL accept bounded, structured business rules for
generation and export without granting arbitrary code execution.

#### Scenario: Valid business rules are supplied

- **GIVEN** a reviewed DatasetSpec and a valid workspace rule file or inline
  rule payload
- **WHEN** generation or export runs
- **THEN** deterministic code applies and validates the rules
- **AND** the bundle contains a business validation report
- **AND** the manifest records the rule fingerprint and validation summary

#### Scenario: Unsafe or ambiguous rules are supplied

- **GIVEN** rules contain unknown fields, dangling references, unsupported
  expressions, raw-looking sensitive literals, excessive input, or both path
  and payload inputs
- **WHEN** the generator MCP server validates the request
- **THEN** it rejects the request before creating output artifacts

### Requirement: Bounded Business Validation Response

MCP business-rule responses SHALL remain metadata-only and bounded.

#### Scenario: Business validation contains row-level failures

- **GIVEN** generated synthetic rows violate one or more configured rules
- **WHEN** generation completes
- **THEN** the MCP response contains only aggregate pass/fail counts, validity,
  the rule fingerprint, and artifact paths
- **AND** detailed bounded errors are written to the workspace report
- **AND** generated rows are not returned inline
