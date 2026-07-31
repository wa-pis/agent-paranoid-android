# Agent Orchestration Specification Delta

## Added Requirements

### Requirement: Provider Example Is Optional And Review Gated

The project SHALL provide an optional real-provider advisor example without
adding that provider SDK to the base installation or bypassing core safety
validation.

#### Scenario: OpenAI proposes a DatasetSpec

- **GIVEN** the OpenAI extra, a configured API credential, and a planned agent
  workspace
- **WHEN** the reference agent requests an OpenAI proposal
- **THEN** package-owned instructions and untrusted profile metadata use
  separate request roles
- **AND** the API request disables response storage and requires a structured
  `AdvisorProposal`
- **AND** incomplete, missing, oversized, or invalid responses fail before
  persistence or generation
- **AND** successful output still requires exact-fingerprint human approval
- **AND** the model receives no source rows, generated rows, or database
  credentials

#### Scenario: Base package is installed

- **GIVEN** an installation without the OpenAI extra
- **WHEN** the base package or deterministic reference advisor is used
- **THEN** the OpenAI SDK is not required or imported
