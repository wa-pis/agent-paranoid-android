# Dataset Validation Delta

## ADDED Requirements

### Requirement: Prepare schema checks within one invocation

Schema validation SHALL prepare effective field/type and primary-key metadata
once per entity and invocation while retaining every existing schema check.
Preparation and validation verdicts SHALL NOT be cached across calls or mutable
specification changes. The policy SHALL apply to specifications from every
supported source without a source-label bypass.

#### Scenario: A specification changes between calls

- **GIVEN** a previous schema-validation call completed
- **WHEN** field names, types, nullability, distributions or the primary key change
- **THEN** the next call prepares checks from the current specification
- **AND** no prior plan or row verdict authorizes the current rows.

### Requirement: Preserve schema decisions and diagnostics

Prepared schema validation SHALL preserve existing entity/count checks, mapping
row support, exact field sets, required values, scalar acceptance, string-pattern
lengths and primary-key type/uniqueness checks. Error ordering and value-free
diagnostics SHALL remain unchanged. Privacy and other mandatory validators SHALL
retain their existing execution and publication boundaries.

#### Scenario: A row contains multiple schema violations

- **GIVEN** synthetic rows contain shape, required-value, type, length or
  primary-key violations
- **WHEN** the prepared schema validator runs
- **THEN** it returns the same ordered diagnostics as the previous implementation
- **AND** no diagnostic includes a failing value.

#### Scenario: A scalar has a parsing edge case

- **GIVEN** a supported scalar includes a boolean, numeric string, non-finite
  float, temporal value or scalar subclass
- **WHEN** schema validation evaluates its declared type
- **THEN** the existing parser and native-scalar acceptance decision is preserved.

#### Scenario: Generated rows reach public CSV export

- **GIVEN** ordinary or explicitly enabled streaming generation uses a fixed seed
- **WHEN** the prepared schema validator participates in mandatory checks
- **THEN** every row retains all existing privacy and validation checks
- **AND** each generator retains its own previous deterministic CSV output
- **AND** atomic publication and private temporary-file cleanup remain enforced.
