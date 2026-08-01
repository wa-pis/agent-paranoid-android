# Dataset Validation Specification

## Purpose

Validate generated datasets with deterministic code so safety and business
expectations do not depend on free-form LLM reasoning.

## Requirements

### Requirement: Schema Validation

Dataset validation SHALL check generated rows against the effective
`DatasetSpec` schema.

#### Scenario: Required fields are missing

- **GIVEN** generated rows for an entity
- **WHEN** a required field from the spec is absent
- **THEN** validation reports the entity, field, and failing condition
- **AND** the validation result is not valid

#### Scenario: Field type does not match

- **GIVEN** generated rows with field values
- **WHEN** a value violates the field data type or declared nullability
- **THEN** validation reports a deterministic failure

### Requirement: Relationship Validation

Dataset validation SHALL verify declared relationships between generated
entities.

#### Scenario: Child rows reference parent rows

- **GIVEN** a child entity has a foreign-key relationship to a parent entity
- **WHEN** validation runs
- **THEN** child references point to generated parent identifiers
- **AND** source identifiers are not required or reused

### Requirement: Constraint Validation

Dataset validation SHALL evaluate executable constraints and rule outcomes.

#### Scenario: Temporal or formula rule is declared

- **GIVEN** a `DatasetSpec` contains temporal, conditional, formula, or
  aggregate constraints
- **WHEN** validation runs
- **THEN** each supported constraint is evaluated by deterministic code
- **AND** failures appear in the validation report

### Requirement: Privacy Validation

Dataset validation SHALL check generated outputs for privacy violations where
the workflow has enough context.

#### Scenario: Sensitive source values are available for comparison

- **GIVEN** source CSV data is available to the local workflow
- **WHEN** generated data is validated
- **THEN** generated rows are checked for copied source rows
- **AND** sensitive raw source values are not accepted in generated output

### Requirement: Reviewable Reports

Validation SHALL produce reviewable artifacts.

#### Scenario: Validation completes

- **GIVEN** generated data and an effective spec
- **WHEN** validation runs
- **THEN** the workflow writes or returns a report with validity, checked
  sections, failures, and relevant row-count context

### Requirement: Validation Settings Have Executable Semantics

Every supported validation setting SHALL affect deterministic validation
behavior and SHALL be recorded in the resulting report or manifest.

#### Scenario: A validation section is disabled

- **GIVEN** a valid `DatasetSpec` disables a supported validation section
- **WHEN** validation runs
- **THEN** that section is omitted according to the documented behavior
- **AND** the report identifies the effective validation settings

#### Scenario: Fail-fast validation finds a failure

- **GIVEN** `fail_fast` is enabled
- **WHEN** an enabled validation section fails
- **THEN** later sections do not run or appear in the report
- **AND** the completed report retains the effective settings

### Requirement: Privacy Assurance Claims Are Bounded

Privacy validation SHALL distinguish deterministic safety checks from
statistical privacy guarantees that the project does not provide.

#### Scenario: Source-row comparison passes

- **GIVEN** source data is available and no complete generated row exactly
  matches a source row
- **WHEN** an operator reviews the result
- **THEN** documentation explains that only exact complete-row reuse was
  checked
- **AND** the result is not presented as differential privacy, anonymity, or
  protection against re-identification
