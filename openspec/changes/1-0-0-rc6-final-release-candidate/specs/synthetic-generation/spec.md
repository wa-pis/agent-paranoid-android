# RC6 Synthetic Output Safety Delta

## ADDED Requirements

### Requirement: Control Artifact Names Are Reserved

Dataset specifications and output writers SHALL reject entity names reserved
for generated control artifacts. The writer SHALL reject the complete entity
set before creating any dataset file.

#### Scenario: Entity collides with the generation manifest

- **GIVEN** a dataset contains an entity named `generation_manifest`
- **WHEN** the specification is validated or rows are written directly
- **THEN** generation fails with a fixed reserved-name error
- **AND** no dataset or control artifact is created

### Requirement: Source-Row Exclusion Uses The Profiled CSV Read

Single-CSV generation SHALL compare generated rows with the complete source
rows observed by the same read that produced the profile. Replacing the source
path after profiling SHALL NOT change the comparison input or permit
publication of a profiled source row.

#### Scenario: Source path is replaced during generation

- **GIVEN** a CSV row has been profiled and generation is in progress
- **WHEN** the source path is atomically replaced before no-copy validation
- **THEN** reuse of the originally profiled row is rejected
- **AND** no generated artifact is published

### Requirement: Dataset Artifact Stems Are Unique

Dataset-row readers SHALL reject duplicate entity stems across supported input
formats before reading any row artifact.

#### Scenario: CSV and JSON artifacts share an entity stem

- **GIVEN** a dataset folder contains `customers.csv` and `customers.json`
- **WHEN** the folder is loaded for validation or recovery
- **THEN** loading fails with a fixed duplicate-name error
- **AND** neither artifact silently replaces the other

### Requirement: Source Categories Never Become Generated Values

CSV-folder profiling SHALL replace source-derived text categories with
collision-safe synthetic rank labels before a profile is cached, returned, or
used for specification inference and generation. Category counts and inferred
conditional rules SHALL remain consistent after replacement. Numeric
distributions SHALL retain their existing type and magnitude semantics.

#### Scenario: A rare category controls a conditional rule

- **GIVEN** a low-cardinality text field contains source values missed by
  sensitive-value heuristics and one value implies another field is required
- **WHEN** the folder is profiled and synthetic rows are generated
- **THEN** the profile, cache, specification, and rows contain no source text
  category
- **AND** the category counts and conditional requirement use the same
  collision-safe synthetic label
- **AND** generation remains deterministic for an explicit seed

### Requirement: Local Profiling Deadline Covers Field Work

CSV-folder profiling SHALL check its monotonic deadline between individual
field processing and field finalization operations.

#### Scenario: A field operation exhausts the deadline

- **GIVEN** a local profile has more than one field to process or finalize
- **WHEN** one field operation exhausts the configured deadline
- **THEN** the next field operation is not started
- **AND** no partial profile cache is published

### Requirement: CSV Output Neutralizes Spreadsheet Formula Markers

CSV export SHALL reject or neutralize string cells beginning with spreadsheet
formula markers such as `=`, `+`, `-`, or `@` when the value could be interpreted
as a formula by common spreadsheet applications. This applies to built-in,
advisor, semantic-provider, and constraint-derived values.

#### Scenario: Formula-like generated cell

- **GIVEN** a generated string begins with a spreadsheet formula marker
- **WHEN** CSV output is serialized
- **THEN** the output contains a literal-safe representation
- **AND** JSON, SQL, and Parquet output contracts remain unchanged
- **AND** a validation test proves the CSV cell is not emitted as an executable
  formula token

### Requirement: Semantic Providers Are Bounded And Synthetic-Only

Semantic providers SHALL run behind an enforceable timeout and cancellation
boundary. With an explicit seed, a provider SHALL either support deterministic
replay or return a seed-bound output fingerprint that can be validated. Names,
addresses, and equivalent identity-bearing values SHALL come only from a
synthetic namespace, and generated output SHALL pass privacy and type checks
after provider execution.

#### Scenario: Provider exceeds its execution deadline

- **GIVEN** a semantic provider does not complete before the invocation
  deadline
- **WHEN** generation handles the provider call
- **THEN** the call is cancelled or isolated and fails with a bounded local
  reason
- **AND** no partial provider output is published

#### Scenario: Provider ignores the requested seed

- **GIVEN** the same specification and seed are replayed
- **WHEN** the provider returns output without deterministic replay support
- **THEN** generation rejects the output or records a failed seed-bound
  fingerprint check
- **AND** an identity-bearing source-like value cannot bypass the post-generation
  privacy check

### Requirement: Single-Entity Publication Has A Verifiable Completion Boundary

Single-entity artifact publication SHALL expose an explicit completion or
read-validation boundary. Interrupted publication SHALL not be reported as
complete, and replacing sibling artifacts in a bundle SHALL require explicit
approval rather than silently following staged-name collisions.

#### Scenario: Publication is interrupted

- **GIVEN** a writer stops after replacing only part of a single-entity bundle
- **WHEN** a reader or recovery path inspects the destination
- **THEN** incomplete output is detectable and is not reported as a complete
  bundle
- **AND** recovery does not follow a symlink outside the approved destination
