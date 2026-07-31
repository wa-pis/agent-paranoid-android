# Agent Orchestration Specification Delta

## Added Requirements

### Requirement: Approval Is Bound To The Reviewed DatasetSpec

Every new agent plan SHALL identify and fingerprint its safe review artifacts,
and approval SHALL require the exact fingerprint of the reviewed effective
`DatasetSpec`.

#### Scenario: Reviewed spec is approved

- **GIVEN** a valid new agent plan and its current spec fingerprint
- **WHEN** approval receives that fingerprint
- **THEN** the stored profile fingerprint and current effective spec
  fingerprint are verified before generation
- **AND** successful generation writes a typed approval receipt containing the
  plan identifier, profile fingerprint, and reviewed spec fingerprint

#### Scenario: Spec changes after review

- **GIVEN** a reviewer recorded the current spec fingerprint
- **WHEN** `dataset_spec.yaml` changes before approval
- **THEN** approval fails before generation
- **AND** no approval receipt or generated dataset is written

#### Scenario: Legacy workspace is approved

- **GIVEN** an agent workspace without plan identity and fingerprints
- **WHEN** approval is attempted
- **THEN** approval fails closed with guidance to create a new plan
