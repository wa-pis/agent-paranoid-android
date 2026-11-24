# Public Contracts Delta

## ADDED Requirements

### Requirement: Retain released behavior during the local improvements port

The port SHALL retain the public 1.7.1 source/output contracts, DatasetSpec 1.1,
DECIMAL, configurable inference, scalable engines, relational/rule evidence,
transformation approval isolation and all resource and privacy boundaries.
Unchanged supported generation SHALL preserve seeded rows and random-call order
within its existing engine. Corrected calculation dependencies SHALL be covered
separately rather than represented as an unchanged-output optimization.

#### Scenario: A released specification is generated after the port

- **GIVEN** an unchanged supported fictional specification and explicit seed
- **WHEN** ordinary or released scalable generation runs
- **THEN** its engine and released type, validation and privacy guarantees remain
- **AND** repeatability and unchanged seeded behavior are verified against 1.7.1.

#### Scenario: A native decimal scalar is validated against a FLOAT field

- **GIVEN** a fictional finite decimal scalar whose text parses as a finite FLOAT
- **WHEN** shared schema validation sees Python, CSV, JSON or Parquet values
- **THEN** it retains the released scalar coercion without mutating input values
- **AND** non-finite FLOAT values remain rejected and privacy checks still run.

### Requirement: Apply shared source privacy without broadening access

Column semantics SHALL use bounded counters and contextual evidence while any
sensitive signal retains source protection. This policy SHALL apply to every
source adapter using the evidence it already provides. Missing evidence SHALL
remain unknown; the port SHALL NOT add source-row reads or broader SQL policy.
Released bounded Parquet inspection and explicit reviewed numeric replacements
SHALL retain their existing safety gates.

#### Scenario: A numeric column has ambiguous phone-like values

- **GIVEN** a neutral numeric column without compatible phone context
- **WHEN** semantics is inferred from its complete available evidence
- **THEN** phone semantics is not forced and sensitivity remains conservative
- **AND** any SSN, card, secret or sensitive null-marker evidence blocks the
  phone-only numeric replacement exception.

#### Scenario: Derived numeric summaries contain a sensitive signal

- **GIVEN** a fictional numeric column whose computed summaries trigger shared privacy policy
- **WHEN** a folder CSV profile is published or cached
- **THEN** it marks the field sensitive and suppresses the numeric distribution
- **AND** cache format 11 rejects earlier profiles rather than reusing stale summaries.

### Requirement: Count complete CSV distinctness with private bounded spill

CSV distinct counting SHALL retain exact counts beyond the old ceilings and
switch from sets to DuckDB only with the optional profiling dependencies.
Scratch SHALL contain private keyed fingerprints, retain finite budgets and be
cleaned before trusted evidence is returned. Backend failure SHALL NOT publish
partial profiles. Source identity and cache authorization SHALL remain bound.

#### Scenario: A large CSV profile crosses the in-memory handoff

- **GIVEN** a bounded fictional input and an explicit profiling budget
- **WHEN** counting switches backend during the existing pass
- **THEN** the complete result matches the set backend
- **AND** raw values are absent from scratch and owned resources are cleaned.

### Requirement: Keep tiled CSV export explicit and checked

The local tiled engine SHALL remain an explicit additive option. It SHALL use
released scalar generation and typed CSV encoding, enforce mandatory checks
before writing, preserve worker-count determinism and atomic bundles, and keep
released engines and unsupported-specification fallback budgets unchanged.

#### Scenario: A specification requires released global behavior

- **GIVEN** embedded rules, relational scenarios or other unsupported tiled CSV behavior
- **WHEN** a streaming policy is requested
- **THEN** the existing checked complete-dataset route retains its limits
- **AND** no validation, approval, source-overlap or publication boundary is bypassed.

### Requirement: Separate historical and current evidence

The port SHALL retain historical benchmark artifacts without modifying their
contents and SHALL label them as measurements of the old source snapshot.
Those measurements SHALL NOT establish performance against 1.7.1.

#### Scenario: Historical results are reviewed after the port

- **GIVEN** a retained old benchmark and its recorded source fingerprints
- **WHEN** it is presented alongside port validation
- **THEN** its baseline, date and rejected candidates remain explicit
- **AND** current correctness evidence is recorded separately.
