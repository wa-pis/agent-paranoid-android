## ADDED Requirements

### Requirement: Generated Utility Evidence Is Bounded and Hash-Bound

Validation SHALL bind additive utility evidence to the canonical effective spec
fingerprint and SHALL distinguish measured generated checks from unknown source
fidelity without changing generation or legacy report readability.

#### Scenario: A declared section is disabled or skipped
- **WHEN** disabled settings or fail-fast prevent relational or temporal validation
- **THEN** active declarations remain counted but their checks are marked not run
- **AND** rejected declarations are excluded from the active count

#### Scenario: Measured zero and no observations differ
- **WHEN** declared relationships have zero resolved references or no checked references
- **THEN** resolution ratios are respectively zero or null
- **AND** generated parent key-domain counts remain distinct from source cardinality
- **AND** source orphan/fan-out rates and unmodeled relationship counts stay unknown

#### Scenario: Native temporal constraints are validated
- **WHEN** an active temporal constraint runs
- **THEN** its report records checked and failed row counts without endpoint values
- **AND** empty data records zero observations without claiming source temporal fidelity
- **AND** collection shares existing work and deadline budgets without rescanning rows

#### Scenario: Evidence is compared with a changed specification
- **WHEN** an operator compares a utility spec hash to the generation manifest or a changed spec
- **THEN** the same effective spec has the same canonical hash and a changed spec differs
- **AND** old reports lacking utility evidence remain readable
