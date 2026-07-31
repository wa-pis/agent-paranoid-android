# Synthetic Generation Delta

## Added Requirements

### Requirement: CLI And MCP Negative Reproducibility

The project SHALL provide a checked-in synthetic example that produces the
same controlled invalid cases through CLI and generator MCP interfaces.

#### Scenario: Equivalent inputs are used

- **GIVEN** the same reviewed spec, business rules, seed, mode, and invalid
  ratio
- **WHEN** generation runs once through CLI and once through generator MCP
- **THEN** both interfaces write identical synthetic row files
- **AND** their business-validation reports contain matching expected and
  observed violation counts
