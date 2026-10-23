# Business rules

## Purpose

Define reviewed conditional formula execution and evidence for source-free
synthetic models, preserving existing privacy, compatibility and resource limits.

## Requirements

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


#### Scenario: Conditional validation evidence
- **WHEN** a formula has a predicate
- **THEN** its result records eligible, evaluated and skipped row counts
- **AND** evaluation failures count as attempted evaluations and failures without source values
- **AND** omitted predicates retain the former serialized rules, hashes and report shape

#### Scenario: Conflicting conditional writers
- **WHEN** a predicate field is a row-rule write target or assignments cannot be proven disjoint
- **THEN** preflight rejects before row mutation or publication
- **AND** disjoint equality/membership branches over one predicate field remain executable

#### Scenario: Conditional safety and budgets
- **WHEN** predicates or formulas consume work or contain literals
- **THEN** schema-bound and schema-less calls enforce existing literal privacy
- **AND** predicates share the invocation work allowance and deadline with expressions
- **AND** exact DECIMAL arithmetic and unsupported-expression rejection remain unchanged

#### Scenario: A fictional EAV model
- **WHEN** a reviewed bounded attribute vocabulary selects synthetic formula branches
- **THEN** generated key domains and exact numeric targets are deterministic for the same ordered spec and seed
- **AND** null values, missing observations and optional declared uniqueness remain distinct
- **AND** no source-row pivot, source-key retention or implicit duplicate merge occurs
