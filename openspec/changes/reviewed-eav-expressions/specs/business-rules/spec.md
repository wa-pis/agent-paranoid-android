## ADDED Requirements

### Requirement: Reviewed Conditional Formula Evaluation

Conditional formulas SHALL use typed predicates and existing deterministic
privacy, numeric and resource enforcement without expanding the expression AST.

#### Scenario: A reviewed predicate is false
- **WHEN** a formula predicate does not select a generated row
- **THEN** the formula does not assign or evaluate that row
- **AND** evidence records a skipped check rather than a successful formula evaluation

#### Scenario: A predicate is omitted
- **WHEN** an existing formula has no predicate
- **THEN** existing execution, serialization and seeded output remain unchanged

#### Scenario: EAV modeling requires row-level operations
- **WHEN** metadata cannot establish a source-free bounded target model
- **THEN** the planner requests an explicit reviewed model or separate proposal
- **AND** it does not pivot source rows, preserve source keys or invent relationship authority
