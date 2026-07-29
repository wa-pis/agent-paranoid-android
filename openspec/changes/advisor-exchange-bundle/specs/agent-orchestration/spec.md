# Agent Orchestration Specification Delta

## Added Requirements

### Requirement: Advisor Exchange Is Self Describing

The agent workflow SHALL provide a versioned provider-neutral exchange that
separates trusted instructions, untrusted request data, and the structured
response schema.

#### Scenario: An AI client exports an exchange

- **GIVEN** a valid awaiting-approval workspace
- **WHEN** advisor request export uses exchange mode
- **THEN** one JSON document contains package-owned trusted instructions
- **AND** the fingerprint-bound request remains marked untrusted
- **AND** the response JSON Schema is generated from `AdvisorProposal`
- **AND** no provider call, workspace write, approval, or generation occurs

#### Scenario: Exchange policy is modified

- **GIVEN** a serialized exchange with changed instructions or response schema
- **WHEN** it is validated as `AdvisorExchange`
- **THEN** validation fails instead of treating the modified policy as trusted
