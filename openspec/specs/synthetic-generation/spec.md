# Synthetic Generation Specification

## Purpose

Generate deterministic synthetic datasets from explicit specs or safe profile
metadata while preserving schema intent, relationships, and safety guarantees.

## Requirements

### Requirement: Deterministic Seeded Output

Synthetic generation SHALL be reproducible from the same effective spec, seed,
row count, mode, and output format.

#### Scenario: Same seed is reused

- **GIVEN** a reviewed `DatasetSpec` and seed
- **WHEN** generation is run twice with the same options
- **THEN** generated values and relationship wiring are deterministic
- **AND** generation artifacts record the seed used

#### Scenario: Seed is changed

- **GIVEN** a reviewed `DatasetSpec`
- **WHEN** generation is run with a different seed
- **THEN** generated rows may differ
- **AND** the output still satisfies the same validation expectations

### Requirement: No Source Row Copying

Synthetic generation SHALL NOT copy, shuffle, duplicate, or export source rows.

#### Scenario: CSV-derived profile drives generation

- **GIVEN** a profile inferred from source CSV files
- **WHEN** synthetic data is generated
- **THEN** source identifiers are regenerated synthetically
- **AND** generated rows are checked against source rows where source data is
  available to the workflow

### Requirement: Reviewable DatasetSpec Contract

Generation and validation SHALL run from a reviewable `DatasetSpec` contract.
No parallel public generation specification is supported.

#### Scenario: Spec is inferred from a profile

- **GIVEN** a safe dataset profile
- **WHEN** a `DatasetSpec` is inferred
- **THEN** it declares entities, fields, row counts, relationships,
  constraints, privacy rules, generation settings, and validation settings
- **AND** users can inspect or edit it before generation

#### Scenario: Removed specification shape is supplied

- **GIVEN** a file with the removed top-level `table` or `tables` shape
- **WHEN** generation or validation is requested
- **THEN** the command fails before rows are processed
- **AND** the error points to the version `0.6.0` migration guide

#### Scenario: Single-CSV workflow writes its effective spec

- **GIVEN** a CSV file is processed by the complete generation workflow
- **WHEN** review artifacts are published
- **THEN** the effective `DatasetSpec` is written as `dataset_spec.json`

### Requirement: DatasetSpec Version Compatibility

DatasetSpec readers SHALL accept only explicitly supported schema versions and
SHALL fail closed on unknown versions.

#### Scenario: Unknown schema version is supplied

- **GIVEN** a DatasetSpec with a `schema_version` not listed as supported
- **WHEN** a file or profile adapter attempts to load it
- **THEN** loading fails before generation or validation
- **AND** the error lists the schema versions supported by the package

#### Scenario: Schema version is deprecated

- **GIVEN** a supported DatasetSpec version is scheduled for removal
- **WHEN** the deprecation is released
- **THEN** the changelog and migration documentation identify the replacement
- **AND** the old version remains readable for at least one feature release and
  90 days unless an urgent security issue requires earlier removal

### Requirement: Bounded Generation

Generation SHALL enforce configured row-count limits before writing output.

#### Scenario: Requested row count is above the limit

- **GIVEN** a configured maximum generation count
- **WHEN** a command or spec requests more rows than allowed for an entity
- **THEN** generation is rejected before partial output is committed

### Requirement: Atomic Output Bundles

Dataset generation SHALL avoid leaving partially assembled output bundles as
successful results.

#### Scenario: Generation bundle is written

- **GIVEN** an output folder is requested
- **WHEN** generation, validation, and manifest creation complete
- **THEN** the folder contains generated data, effective spec, validation
  report, and generation manifest
- **AND** input and output paths are distinct

### Requirement: Cross-Table Average Reconciliation

Aggregate mappings SHALL support deterministic average reconciliation across
a declared parent-child relationship.

#### Scenario: Child values include nulls

- **GIVEN** an average mapping from a parent field to a numeric child field
- **WHEN** generated child rows contain numeric and null values
- **THEN** the parent field equals the average of non-null numeric values
- **AND** validation applies the same rule

#### Scenario: Trino average consistency is profiled

- **GIVEN** allowlisted parent and child tables
- **WHEN** average mapping profiling is requested
- **THEN** the server executes a fixed grouped `avg` query
- **AND** returns only aggregate consistency metadata

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
