# Synthetic Generation Delta

## ADDED Requirements

### Requirement: Preserve generation semantics during dispatch optimization

Generation dispatch optimizations SHALL preserve previous values, types, errors,
random and Faker state transitions for the same effective specification, seed
and engine. They SHALL retain null, invalid, identifier, sensitive, provider and
categorical priority, and SHALL apply equally to every source-derived spec.

#### Scenario: Ordinary and tiled generation use the same effective inputs

- **GIVEN** a fictional specification and explicit seed for a supported engine
- **WHEN** the optimized dispatch generates values
- **THEN** its rows and serialized CSV match that engine's previous results
- **AND** privacy, schema, relationship and business-rule checks remain active.

#### Scenario: A specification changes between calls

- **GIVEN** a specification's type, distribution or privacy metadata is edited
- **WHEN** a later generation call uses the changed specification
- **THEN** the changed metadata is observed without stale cached decisions
- **AND** random draws and provider requests match the previous implementation.

### Requirement: Retain bounded checked generation and publication

Generation optimization SHALL retain configured budgets, mandatory validation,
strict privacy checks, private temporary files and atomic publication. Performance
evidence SHALL preserve every paired observation, separate seed namespaces and
unchanged output-integrity checks.

#### Scenario: Generation or validation fails during export

- **GIVEN** an export encounters a worker, budget, privacy or validation failure
- **WHEN** the operation cannot safely complete
- **THEN** no partial trusted output is published
- **AND** existing destination protection and owned-resource cleanup remain active.
