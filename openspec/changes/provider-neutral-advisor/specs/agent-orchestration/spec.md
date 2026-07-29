# Agent Orchestration Specification Delta

## Added Requirements

### Requirement: Advisor Integration Is Provider Neutral

The agent workflow SHALL expose a typed provider-neutral interface that accepts
safe profile metadata and proposes a structured `DatasetSpec`.

#### Scenario: A model adapter proposes a DatasetSpec

- **GIVEN** a profile that passes the existing profile safety checks
- **WHEN** a provider adapter receives an advisor request
- **THEN** the request contains safe metadata, a deterministic baseline spec,
  and their SHA-256 fingerprints
- **AND** it contains no source rows, generated rows, credentials, or provider
  SDK objects

### Requirement: Advisor Output Is Untrusted And Review Only

Model-produced proposals SHALL be validated before they can enter the reviewed
generation workflow.

#### Scenario: A valid structured proposal is returned

- **GIVEN** a proposal bound to the request fingerprints
- **WHEN** the core validates it
- **THEN** Pydantic validates the full `DatasetSpec`
- **AND** schema identity and core-owned safety settings remain unchanged
- **AND** the result requires human approval and performs no generation

#### Scenario: A proposal weakens a safety boundary

- **GIVEN** a proposal that removes fields, weakens sensitive or identifier
  classification, changes privacy settings, or embeds raw sensitive values
- **WHEN** the core validates it
- **THEN** validation fails before persistence or generation

### Requirement: Advisor Metadata Is Treated As Untrusted Data

Profile names, descriptions, and safe distribution values SHALL be marked and
handled as untrusted data rather than model instructions.

#### Scenario: Profile metadata contains instruction-like text

- **GIVEN** an entity or field name containing instruction-like text
- **WHEN** an advisor request is built
- **THEN** the text remains structured metadata
- **AND** the request policy tells provider adapters to treat profile text as
  data
