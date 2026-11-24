# Streaming CSV Export

## ADDED Requirements

### Requirement: Explicit large CSV execution option

The public bundle exporter SHALL accept an optional typed streaming policy and
the spec-only `generate` CLI SHALL accept `--stream-csv` with bounded worker
selection. Ordinary generation SHALL retain its default execution and seed
behavior. The option SHALL add no runtime dependency or installation extra.

#### Scenario: Export an independent large CSV entity

- **GIVEN** a safe valid-mode specification with one entity, no relationships,
  no constraints and no business-rule applier
- **WHEN** the caller explicitly requests CSV streaming with sufficient finite
  row/cell/time/output bounds
- **THEN** ordered tiles are validated and serialized without retaining the
  complete generated dataset or CSV text
- **AND** the result remains a metadata/validation summary.

#### Scenario: CLI worker selection is explicit

- **GIVEN** the spec-only CLI route
- **WHEN** `--stream-csv` is supplied
- **THEN** at most 1,000,000 rows, 25,000,000 cells and four workers are permitted
- **AND** the default worker count is four and `--workers` without the flag fails.

#### Scenario: CLI streaming selects CSV explicitly

- **GIVEN** a saved specification with any output-format default
- **WHEN** `--stream-csv` is supplied without `--format`
- **THEN** CSV is selected
- **AND** an explicit non-CSV format with the flag is rejected.

#### Scenario: Python policy receives a non-CSV format

- **GIVEN** an explicit Python streaming policy
- **WHEN** the effective output format is not CSV
- **THEN** the exporter rejects the combination before generation.

#### Scenario: No optional dependency is installed

- **GIVEN** an isolated base installation without PyArrow or DuckDB
- **WHEN** eligible CSV streaming is requested
- **THEN** generation, validation and bundle export succeed using the base package.

### Requirement: Preserve global solving and source boundaries

Specifications that need relationships, constraints, multiple entities,
non-valid modes or a business-rule applier SHALL use the existing complete
generation and validation path. Streaming-specific bounds SHALL NOT enlarge
fallback runs. Source-profile, review/approval and MCP routes SHALL retain their
current source-overlap checks and execution behavior.

#### Scenario: A relationship or business rule needs the existing pipeline

- **GIVEN** a specification or callback requiring global solving
- **WHEN** CSV streaming is requested
- **THEN** the existing generator and complete validation/business-rule path run
- **AND** ordinary generation limits still apply.

#### Scenario: The source-profile CLI route receives the flag

- **GIVEN** a `generate --profile` request
- **WHEN** `--stream-csv` is also supplied
- **THEN** the command rejects the unsupported combination before generation.

### Requirement: Retain mandatory checks and atomic publication

Streaming SHALL enforce schema and privacy checks before any generated tile is
written, regardless of report settings, plus global key uniqueness and final
row counts. It SHALL preserve safe CSV formatting, configured time/byte budgets,
existing artifact names and atomic bundle publication. Failures SHALL expose no
generated values and SHALL not publish a partial trusted bundle.

#### Scenario: Invalid data crosses a tile boundary

- **GIVEN** a duplicate primary key in another tile or an invalid generated value
- **WHEN** the stream validates that input
- **THEN** global uniqueness or mandatory schema/privacy enforcement fails
- **AND** no partial bundle is published.

#### Scenario: Output or execution fails

- **GIVEN** an owned worker failure, cancellation, I/O failure or exhausted bound
- **WHEN** streaming cannot finish successfully
- **THEN** owned workers are stopped and joined and incomplete staging is cleaned
- **AND** the existing destination is protected by the current publication policy.

### Requirement: Record reproducible tiled CSV identity

Eligible streaming exports SHALL use `tiled-v1` fixed logical tiles and record
the selected engine in the manifest's existing
`reproducibility.generator_algorithm_version` field. For a fixed specification,
seed, engine and dependency snapshot, worker count SHALL NOT change CSV bytes.
Default and fallback exports SHALL retain legacy seed/version behavior.

#### Scenario: Compare complete and streaming tiled output

- **GIVEN** an eligible specification, explicit seed and fixed dependency versions
- **WHEN** full tiled generation and streaming run with one, two and four workers
- **THEN** CSV bytes match, including ordering and a partial final tile
- **AND** schema, privacy, global key/count checks and safe CSV formatting remain.
