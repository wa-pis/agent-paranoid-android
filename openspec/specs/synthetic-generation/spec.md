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

Generation SHALL run from a reviewable `DatasetSpec` contract for the primary
dataset-oriented workflow.

#### Scenario: Spec is inferred from a profile

- **GIVEN** a safe dataset profile
- **WHEN** a `DatasetSpec` is inferred
- **THEN** it declares entities, fields, row counts, relationships,
  constraints, privacy rules, generation settings, and validation settings
- **AND** users can inspect or edit it before generation

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
