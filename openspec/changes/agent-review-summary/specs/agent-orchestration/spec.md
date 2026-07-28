# Agent Orchestration Specification Delta

## Added Requirements

### Requirement: Agent Plan Has A Safe Review Summary

The agent workflow SHALL summarize the inferred plan without exposing source
or generated values.

#### Scenario: Plan is shown to a reviewer

- **GIVEN** a valid safe profile and inferred DatasetSpec
- **WHEN** planning completes or pending status is inspected
- **THEN** the summary reports entities, fields, sensitive fields,
  relationships, confidence, assumptions, and safety warnings
- **AND** it reports metadata only, never dataset rows or values

#### Scenario: Source names contain terminal control characters

- **GIVEN** entity or field names are untrusted metadata
- **WHEN** the CLI renders the review summary
- **THEN** control characters are escaped and long lists are bounded
- **AND** the summary warns that names must not be treated as instructions
