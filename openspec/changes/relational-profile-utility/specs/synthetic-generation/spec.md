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

#### Scenario: Declared scalar primary key has no identifier suffix
- **GIVEN** authorized PostgreSQL metadata declares a single INTEGER or STRING primary key
- **WHEN** a profile is inferred into a generation specification
- **THEN** the key is a synthetic identifier regardless of its name
- **AND** its type and sensitivity classification are retained
- **AND** seeded generation produces unique synthetic keys without fetching source keys

#### Scenario: Only part of a composite primary key is authorized
- **GIVEN** the column allowlist exposes one component of a composite primary key
- **WHEN** PostgreSQL profiling reads bounded catalog metadata
- **THEN** the complete key arity causes an explicit unsupported-key rejection before aggregate scans
- **AND** no unauthorized component name or source key value is returned

#### Scenario: Declared scalar key has an unsupported generation type
- **WHEN** a declared PostgreSQL primary key has a type other than INTEGER or STRING
- **THEN** profiling requests a reviewed generation specification instead of inferring incompatible synthetic identifiers
