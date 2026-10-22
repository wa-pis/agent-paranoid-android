## ADDED Requirements

### Requirement: Reviewable Relational Utility Evidence

Relational planning SHALL distinguish observed facts, unreviewed hypotheses and
approved executable relationships. Unknown fidelity SHALL NOT be reported as a
successful source-fidelity check.

#### Scenario: No logical relationship has been declared
- **WHEN** generation validates an otherwise valid specification without edges
- **THEN** relationship coverage is untested rather than measured perfect integrity
- **AND** any inferred candidate requires review before execution

#### Scenario: Parent and child sizes differ
- **GIVEN** reviewed counts and an approved foreign key
- **WHEN** data is generated with a fixed seed
- **THEN** non-null child references resolve to generated parent keys
- **AND** independent identifier domains do not collide by row position

#### Scenario: Composite primary-key metadata is received
- **WHEN** the planner cannot represent the complete key
- **THEN** it reports the unsupported structure without certifying one component as unique
