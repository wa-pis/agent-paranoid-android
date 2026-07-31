# Synthetic Generation Delta

## Added Requirements

### Requirement: Controlled Negative Rule Coverage

Negative and mixed generation SHALL create deterministic, validator-observable
violations across supported field and row business rules.

#### Scenario: Several rules apply to one table

- **GIVEN** a table with multiple supported field and row rules
- **WHEN** enough rows are selected for invalid generation
- **THEN** invalid cases are distributed across the applicable rules
- **AND** repeated generation with the same seed produces identical rows
- **AND** business validation reports the intentional failures

#### Scenario: A numeric bound receives a non-numeric value

- **GIVEN** a field rule with a numeric minimum or maximum
- **WHEN** validation receives a non-null, non-empty, non-numeric value
- **THEN** the bound validation fails closed
