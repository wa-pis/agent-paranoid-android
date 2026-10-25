# Dataset Validation Specification

## Purpose

Validate generated datasets with deterministic code so safety and business
expectations do not depend on free-form LLM reasoning.

## Requirements

### Requirement: Row-Aware Privacy Revalidation

The enabled privacy section SHALL inspect supplied row values as well as spec
safety, using the same policy as generation and without exposing failing values.
Declared numeric CSV representations SHALL be classified as numeric values.

#### Scenario: A generated artifact has been modified

- **WHEN** a supplied string violates the synthetic sensitive-value policy
- **THEN** privacy validation fails without echoing its contents.

### Requirement: Rejected Rules And Nullable References

Rejected relationships and constraints SHALL not be validated. Null references
SHALL pass only for nullable child fields. Required identifiers SHALL reject null
or empty values even when they are not the primary key. String-pattern bounds
SHALL be checked against the complete supplied value.

#### Scenario: A rejected rule is retained for review

- **WHEN** a reviewed relationship or constraint has rejected status
- **THEN** validation skips that rule without treating it as an active invariant
- **AND** active schema and nullable-reference checks still apply

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

### Requirement: Business-Rule Format Is Reviewable And Executable

The standalone BusinessRules format SHALL have a JSON Schema generated from
its runtime model and an annotated, source-free example covering every current
rule family, condition predicate and optional model field. The example SHALL
include a compatible DatasetSpec and executable generation/validation evidence.
Documentation SHALL distinguish assignment from checks, structural schema
validation from runtime privacy/reference validation, and approximate scenario
weights from exact quotas. This does not change runtime rule semantics.

#### Scenario: Reader explores the complete business-rule format

- **GIVEN** the complete checked-in example and its companion specification
- **WHEN** generation runs in valid mode with the documented seed
- **THEN** native and business-rule validation succeed without source data
- **AND** rules can be supplied separately or embedded in the reviewed spec

#### Scenario: Models change without updating the reference

- **GIVEN** a new rule family, model field or changed structural contract
- **WHEN** schema freshness and example contract tests run
- **THEN** missing schema/example coverage fails the checks
- **AND** unsupported formula or condition capabilities are not inferred
  from JSON Schema alone

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

### Requirement: Explicit Relational Scenario Reconciliation

A spec containing relational_scenarios SHALL receive mandatory final schema,
privacy, native/business constraint and exact requested/observed relationship
reconciliation even when optional validation settings are disabled. Evidence
SHALL bind the effective spec and resolved sizes, return counts without keys,
and distinguish matching controlled-invalid expectations from dataset validity.

#### Scenario: Controlled invalid counts match the declaration
- **WHEN** generated missing-parent references and fan-out match every declared quota
- **THEN** expectations_met may be true while ordinary validity and validation_valid remain false
- **AND** SQL export requiring valid foreign keys rejects before publication

#### Scenario: A writer receives changed rows
- **WHEN** final rows violate a quota, an unscoped relationship or a mandatory invariant
- **THEN** the writer rejects before publishing replacement artifacts

### Requirement: RC3 feedback contract
Relationship validation SHALL report zero checked and passed links when none are declared. It SHALL report per-link resolution and cardinality without key values. Active links SHALL have matching field types and a unique binding per child field.

#### Scenario: Deterministic enforcement
- **WHEN** the corresponding CLI or direct service is invoked
- **THEN** the contract is enforced before publication and tested with fictional inputs

### Requirement: Conservative inferred field bindings
CSV inference SHALL require matching descriptive identifier names and field
types. Generic keys and multiple candidate parent domains SHALL require explicit
reviewed declarations. Old cached inferences SHALL be invalidated.

#### Scenario: Unrelated numeric domains overlap
- **GIVEN** customer_id and product_id contain the same fictional integers
- **WHEN** folder profiling runs
- **THEN** no relationship is inferred between those fields
