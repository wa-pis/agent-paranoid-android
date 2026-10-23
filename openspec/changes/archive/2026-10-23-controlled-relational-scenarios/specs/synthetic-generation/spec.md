## ADDED Requirements

### Requirement: Reviewed Controlled Relational Scenarios

Optional relational scenarios SHALL be explicit synthetic declarations bound to
the effective specification and resolved entity sizes, separate from ordinary
valid foreign-key generation.

#### Scenario: An explicit scenario requests controlled orphans
- **WHEN** a reviewed scenario selects an active edge and an eligible exact orphan count
- **THEN** only controlled-invalid mode may generate those synthetic missing keys
- **AND** validation records expected and observed invalid references without claiming validity
- **AND** valid mode rejects the request before publication

#### Scenario: A generated fan-out allocation is requested
- **WHEN** a reviewed allocation names generated parent ordinals and child counts
- **THEN** its totals must match eligible generated children within existing budgets
- **AND** impossible, ambiguous or conflicting allocations reject before publication
- **AND** no source values, row mappings or inferred source histogram are consumed

#### Scenario: No relational scenario is supplied
- **WHEN** callers omit the new declaration
- **THEN** existing seeded assignment, count and mode contracts remain unchanged
