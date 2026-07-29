# Agent Orchestration Specification Delta

## Added Requirements

### Requirement: Advisor Proposals Enter The Existing Review Gate

The agent workflow SHALL persist validated advisor proposals as review
artifacts and SHALL require the normal reviewed-spec approval before
generation.

#### Scenario: A pending workspace receives a valid proposal

- **GIVEN** an awaiting-approval agent workspace
- **WHEN** a provider-neutral advisor returns a valid proposal
- **THEN** `advisor_review.json` records the safe request, proposal, and
  proposed-spec fingerprint
- **AND** `dataset_spec.yaml` contains the proposed spec
- **AND** status reports the current spec fingerprint and review summary
- **AND** no generated dataset exists

### Requirement: Advisor Handoff Is Recoverable And Conflict Safe

Advisor persistence SHALL recover from interruption without recalling the
provider or overwriting a conflicting human edit.

#### Scenario: Persistence stops after the review artifact

- **GIVEN** a valid `advisor_review.json` and the unchanged baseline spec
- **WHEN** advisor handoff is retried
- **THEN** the persisted proposal is revalidated and applied
- **AND** the provider is not called again

#### Scenario: The spec changes after advisor review

- **GIVEN** a persisted advisor review
- **WHEN** `dataset_spec.yaml` matches neither its baseline nor its proposed
  fingerprint
- **THEN** handoff fails without modifying the spec
