## ADDED Requirements

### Requirement: Portable Agent Guidance Matches Installed Capabilities

Prompt templates and bundled skills SHALL distinguish synthetic generation from
one-to-one mixed-origin transformation, and SHALL use discovered installed CLI
help and MCP schemas as capability authority. Instructions SHALL require review
of the exact current synthetic specification fingerprint before approval, and
SHALL preserve local-only controlling-TTY issuance of preservation receipts.

#### Scenario: Agent loads a synthetic workflow

- **GIVEN** a file, related CSV folder, safe profile or allowlisted Trino source
- **WHEN** the agent uses its matching instructions
- **THEN** it plans and inspects before human review of the exact specification
- **AND** it forwards only supported parameters to the selected CLI/MCP route
- **AND** it inspects status after interruption instead of blindly regenerating

#### Scenario: Agent loads a transformation workflow

- **GIVEN** an explicitly requested one-to-one transformation
- **WHEN** field preservation is proposed
- **THEN** instructions require matching local operator approval before execution
- **AND** no chat confirmation, simulated TTY or MCP issuer replaces that receipt
- **AND** output summaries remain value-free and label the result mixed-origin

### Requirement: Installed Wheels Include Complete Offline Agent Resources

Built wheels SHALL include prompt templates, skills, their UI metadata and linked
skill references. Package installation SHALL NOT automatically register skills
with another agent or change its configuration. Installed-package checks SHALL
verify nonempty resources and offline discovery of the recommended CLI routes.

#### Scenario: Agent uses only an installed package

- **GIVEN** a newly built wheel with no source checkout
- **WHEN** its resource directories are located through importlib.resources
- **THEN** instructions and skill references are available without network access
- **AND** CLI discovery succeeds without a provider or database connection
- **AND** missing templates, UI metadata or references fail package verification
