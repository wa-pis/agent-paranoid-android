# Dataset Capacity Specification Delta

Implemented subsets are run-local distribution preparation and standalone
Python `tiled-v1` execution. Shared forecasts, hard memory/output/temp accounting,
CLI/MCP review, manifests and atomic streaming publication remain proposed.

## ADDED Requirements

### Requirement: Comparable streaming backend evidence

The benchmark-only streaming experiment SHALL share the tiled producer,
mandatory privacy/schema checks and safe CSV sink between Python/Arrow and
DuckDB. It SHALL check whole-run row counts and key uniqueness, record stages
and concurrent process-tree RSS, and compare exact CSV bytes with the complete
materialized `tiled-v1` reference. It SHALL NOT enable a public streaming route.

#### Scenario: Compare streaming sinks

- **GIVEN** the fictional valid-mode 25-field specification and seed 42
- **WHEN** each sink runs three times at 100,000 and 750,000 rows
- **THEN** every run passes mandatory checks and the complete CSV hash matches
- **AND** the evidence distinguishes overlapping worker compute, parent stages,
  growing Python key state and DuckDB buffer limits from total process RSS.

#### Scenario: Fail safely before publication

- **GIVEN** an unsupported global rule or an invalid generated batch
- **WHEN** the benchmark attempts streaming
- **THEN** unsupported rules fail before generation and invalid rows never enter
  Arrow/DuckDB or the output file
- **AND** native failures expose no generated values and private staging is cleaned.

### Requirement: Explicit tiled Python process generation

The standalone Python API SHALL use a versioned `tiled-v1` stream with fixed
4,096-row logical tiles, derived RNG/Faker seeds and absolute row indices.
One, two and four workers SHALL produce identical ordered rows for the same
specification, seed and dependency versions. The ordinary legacy API SHALL
retain its existing seed behavior; tiled results need not equal legacy results.

#### Scenario: Compare worker counts

- **GIVEN** the same typed specification and explicit `tiled-v1` seed
- **WHEN** standalone generation runs with one, two and four worker processes
- **THEN** rows and ordering are identical, including partial final tiles
- **AND** global constraints, schema and privacy are validated before return.

#### Scenario: Explicit Python large-run bounds

- **GIVEN** 750,000 rows with 25 fields
- **WHEN** the caller supplies sufficient finite row/cell/time bounds
- **THEN** the standalone Python path can execute within those workload bounds
- **AND** ordinary generation and database/profiling caps remain unchanged.

#### Scenario: Python path has no publication authority

- **GIVEN** standalone process generation fails or is cancelled
- **WHEN** the coordinator handles that outcome
- **THEN** workers are stopped and joined and no partial dataset is returned
- **AND** no bundle, manifest, approval receipt or source-row output is published.

### Requirement: Reuse prepared distribution metadata within a call

Ordinary generation and schema validation SHALL prepare each field's typed distribution
once per entity and invocation, preserving seeded output and all existing checks.
Prepared metadata SHALL NOT be shared between invocations.
The opt-in tiled engine SHALL prepare distributions once per logical tile.

#### Scenario: Seeded compatibility after preparing distributions

- **GIVEN** a valid synthetic specification and an explicit seed
- **WHEN** generation reuses prepared distribution models
- **THEN** rows and random-call order match the unprepared implementation
- **AND** schema and privacy checks still run before generated rows are returned.

#### Scenario: Distribution metadata changes between invocations

- **GIVEN** a specification whose distribution dictionary was edited after a call
- **WHEN** generation or schema validation runs again
- **THEN** the new call prepares and uses the current distribution metadata.

### Requirement: Explainable storage forecasts

The system SHALL forecast per-entity and total file bytes for CSV, JSON and
Parquet with explicit settings, low/expected/high values, method, confidence
and assumptions. It SHALL distinguish logical database payload from optional
engine-specific base-table storage and exclude indexes and auxiliary storage.
Unknown physical layouts SHALL be reported as unknown, not as CSV size.

#### Scenario: Compare output formats without generating a dataset

- **GIVEN** a reviewed typed specification, row counts and encoding settings
- **WHEN** the caller requests estimates without calibration
- **THEN** the system returns format-specific ranges and DB payload assumptions
- **AND** it creates no generated dataset and exposes no source rows.

#### Scenario: Unknown database storage model

- **GIVEN** unsupported engine types or insufficient layout information
- **WHEN** database size is estimated
- **THEN** the system identifies the missing assumptions and unknown physical size
- **AND** retains only estimates it can support.

### Requirement: Evidence-based duration forecasts

The system SHALL estimate end-to-end time with stage costs and uncertainty
using applicable measured evidence or explicitly report insufficient evidence.
Synthetic calibration SHALL be opt-in, bounded, isolated from generation random
streams and publication, and SHALL not expose generated or source rows.

#### Scenario: Fresh machine with no calibration

- **GIVEN** no compatible benchmark or calibration evidence
- **WHEN** the caller asks how long generation will take
- **THEN** the result reports unavailable or low-confidence time with reasons
- **AND** offers bounded calibration without claiming a precise duration.

#### Scenario: Calibrated generation

- **GIVEN** relevant local calibration and matching engine/spec/settings
- **WHEN** a larger dataset is planned and generated
- **THEN** the estimate includes generation, checks, validation and writing
- **AND** observed progress does not report completion before final publication.

### Requirement: Explicit large-dataset budgets

The system SHALL support an explicit reviewed generation policy capable of
750,000 rows with 25 columns, subject to finite memory, cells, output, temporary
disk and time budgets. It SHALL preserve conservative unattended defaults,
separate read-only database budgets and independent actual resource accounting.

#### Scenario: Default row cap would block requested scale

- **GIVEN** a request for 750,000 rows exceeding the default generation cap
- **WHEN** the user plans a large run
- **THEN** the system identifies the limiting budget and accepts an explicit
  bounded large-run policy through the public interface
- **AND** never silently raises budgets or approves the run.

#### Scenario: Reviewed settings change

- **GIVEN** an approved plan
- **WHEN** counts, semantics or accepted resource policy change
- **THEN** previous approval cannot authorize the changed plan
- **AND** volatile ETA updates alone do not invalidate approval.

### Requirement: Distinct deterministic scalable generation

The scalable engine SHALL create fresh synthetic rows with exact requested
counts and declared uniqueness, independent of worker count and operational
grouping of complete logical tiles. Tile width is an engine-version constant.
It SHALL preserve relationships, business rules, privacy and source-reuse checks.
Legacy engine seed behavior SHALL remain available and unchanged. Future bundle
integration SHALL record engine/version and execution policy in manifests;
the initial standalone Python API creates no bundle or manifest.

#### Scenario: Different worker counts

- **GIVEN** a scalable-engine spec with a unique synthetic key and explicit seed
- **WHEN** it is generated with one, two or four workers and operational grouping
  of complete fixed logical tiles
- **THEN** logical rows and ordering are identical with no overlapping key ranges
- **AND** no completed batch is duplicated to reach the target count.

#### Scenario: Impossible distinctness

- **GIVEN** requested unique rows or keys exceed available domain capacity
- **WHEN** the plan is checked or generation reaches a bounded feasibility limit
- **THEN** the system returns an actionable constraint error
- **AND** does not publish duplicates or retry without a bound.

### Requirement: Bounded parallel execution and publication

Parallel execution SHALL cap workers and in-flight batches, enforce shared
budgets and preserve atomic publication when integrated with bundle workflows.
The initial Python API only returns fully collected and validated rows; it does
not perform publication. Unsupported global constraints SHALL
use a bounded safe fallback or be rejected explicitly before output publication.

#### Scenario: Worker failure or budget exhaustion

- **GIVEN** an active large dataset run
- **WHEN** a worker fails, cancellation occurs or a resource budget is exhausted
- **THEN** children are stopped and reaped, staging is cleaned or safely recoverable
- **AND** no partial final dataset is published or existing output overwritten.

### Requirement: Measured performance and forecast acceptance

The change SHALL provide reproducible synthetic accuracy and performance
evidence using the matrix and thresholds in design.md, including 750,000
distinct rows with 25 columns on recorded multicore hardware. User-reported
20-minute timing SHALL remain identified as unverified until reproduced.

#### Scenario: Performance acceptance

- **GIVEN** baseline and optimized runs on the same recorded reference host
- **WHEN** benchmark acceptance is evaluated
- **THEN** evidence includes repeated end-to-end timings, 1/2/4-worker results,
  actual output bytes, forecast errors and process-tree memory
- **AND** unmet targets are reported rather than marked complete.
