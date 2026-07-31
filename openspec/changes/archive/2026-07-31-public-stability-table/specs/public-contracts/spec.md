# Public Contracts Delta

## Added Requirements

### Requirement: Public Stability Map

The documentation SHALL identify the stability status, owner, compatibility
rule, and contract gate for every supported public integration surface.

#### Scenario: A maintainer reviews a public change

- **GIVEN** a proposed change affects Python imports, CLI, MCP, `DatasetSpec`,
  advisor JSON, or generated artifacts
- **WHEN** the maintainer consults the stability map
- **THEN** the affected owner and contract gate are identifiable
- **AND** the change can be classified as additive or breaking

#### Scenario: An experimental integration is used

- **GIVEN** a provider adapter or runnable example is not part of the stable
  deterministic core
- **WHEN** its compatibility status is reviewed
- **THEN** it is clearly labelled experimental
- **AND** core safety requirements still apply
