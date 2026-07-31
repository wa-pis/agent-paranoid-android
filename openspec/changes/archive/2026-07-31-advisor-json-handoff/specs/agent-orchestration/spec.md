# Agent Orchestration Specification Delta

## Added Requirements

### Requirement: Advisor Exchange Has A Provider-Neutral JSON Boundary

The agent workflow SHALL export a safe advisor request and apply an untrusted
structured proposal without requiring a model-provider SDK.

#### Scenario: An AI client requests advisor input

- **GIVEN** an awaiting-approval workspace without an existing advisor review
- **WHEN** the advisor request is exported
- **THEN** one versioned JSON document contains safe metadata, a baseline
  `DatasetSpec`, and their fingerprints
- **AND** it contains no source rows, generated rows, credentials, or provider
  objects
- **AND** the workspace is not modified

#### Scenario: An AI client submits a proposal

- **GIVEN** a bounded regular JSON file containing a proposal bound to the
  exported fingerprints
- **WHEN** the proposal is applied
- **THEN** the existing advisor validation and atomic review persistence run
- **AND** status remains awaiting approval
- **AND** no generated dataset exists

### Requirement: External Advisor Application Is Retryable And Fail Closed

External proposal application SHALL resume the same validated exchange after
interruption and SHALL reject stale, different, or conflicting content.

#### Scenario: Proposal application is retried

- **GIVEN** a persisted review artifact and an unchanged baseline spec
- **WHEN** the same proposal is applied again
- **THEN** the proposed spec is applied without another provider call

#### Scenario: Proposal or workspace no longer matches

- **GIVEN** stale fingerprints, different proposal content, a conflicting
  spec edit, malformed input, a link, or an oversized file
- **WHEN** proposal application is attempted
- **THEN** it fails before generation or approval
