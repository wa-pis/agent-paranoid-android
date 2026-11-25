# Streaming Exact CSV-Folder Profiling

## Requirements

### Requirement: Bounded Distinct-State Handoff

CSV-folder profiling SHALL retain Python sets while the sum of per-field
distinct fingerprints for one entity is at most 1,000,000. Above that threshold
it SHALL drain the sets and count remaining normalized non-null values through
one streaming DuckDB query. It SHALL NOT reopen the CSV or repeat inference on
already processed cells. The threshold SHALL NOT cap the resulting exact count.

#### Scenario: Handoff occurs within a row

- **GIVEN** one field crosses the per-entity threshold partway through a CSV row
- **WHEN** profiling continues through DuckDB
- **THEN** the triggering cell is included exactly once in the counts
- **AND** every remaining cell receives the existing type, sensitivity, sample
  and budget processing exactly once.

#### Scenario: A large low-cardinality input remains small in memory

- **GIVEN** many permitted source rows whose field sets remain below the threshold
- **WHEN** profiling completes
- **THEN** it uses sets without importing the optional backend.

### Requirement: Complete Profile Equivalence

The set and DuckDB paths SHALL produce identical completed profile content,
profile/spec fingerprints and cache round trips for the same permitted source
and settings. Exact ratios, identifier pools, key candidates, sensitivity,
distributions, local-category policy, relationships and constraints SHALL keep
their existing semantics. Cache format 5 SHALL remain valid.

#### Scenario: Duplicates arrive after handoff

- **GIVEN** a repeated identifier whose duplicate occurs after the handoff
- **WHEN** the complete folder is profiled
- **THEN** its exact distinct count and identifier pool match the set path
- **AND** it receives no false unique-key certification.

### Requirement: Keyed Private Scratch

Only integer field ordinals and HMAC-SHA256 tokens derived under a fresh
memory-only 32-byte invocation key SHALL enter Arrow and DuckDB. Source values,
field names, ordinary SHA-256 fingerprints and the key SHALL NOT enter spill.
Scratch SHALL use a fresh private directory, `0700` on POSIX. Profiles, caches,
logs, exceptions and transport responses SHALL contain neither keys nor tokens.

#### Scenario: A count spills to disk

- **GIVEN** an exact-distinct query needs more buffer memory
- **WHEN** DuckDB creates temporary files
- **THEN** files remain beneath the private invocation directory
- **AND** their input tokens cannot be tested against source candidates using
  an unkeyed hash or linked to a separate invocation's tokens.

### Requirement: Fixed Bounded Local Execution

The backend SHALL use an in-memory database, one fixed grouped exact-distinct
query, lazy batches of at most 50,000 tokens, a 128 MiB buffer limit, a 2 GiB
spill limit, one query thread and one asynchronous I/O thread. External access,
extension autoload/install, Python replacement scans and logging SHALL be
disabled, and configuration SHALL be locked before the count query. The buffer
setting SHALL NOT be described as a hard total-process memory limit.

Existing input-byte, row, cell, sample and deadline budgets SHALL remain in
force. A native query deadline SHALL use the invocation's remaining time, and
post-query deadline checks SHALL prevent overdue publication.

#### Scenario: Native aggregation runs beyond its deadline

- **GIVEN** the producer has finished and native aggregation remains busy
- **WHEN** the remaining invocation time expires
- **THEN** the query is interrupted and the operation fails as a safe profile
  deadline failure rather than returning partial trusted counts.

### Requirement: Safe Failure And Cleanup

The reader and connection SHALL close and scratch SHALL be removed before
counts are returned. Backend or cleanup failure SHALL produce a value-free
error without publishing a partial profile or trusted cache. Original safe
source-budget errors and cancellation SHALL retain their meaning through Arrow
exception wrapping. Cleanup after abrupt process death is not guaranteed.

#### Scenario: Producer or cleanup fails

- **GIVEN** profiling has handed off to the optional backend
- **WHEN** source work, the backend or scratch cleanup fails
- **THEN** the caller receives no source-bearing backend detail
- **AND** no partial profile/cache is published as complete.

### Requirement: Optional Integration Availability

The `profiling` extra SHALL provide DuckDB and PyArrow without adding them to
base dependencies. `all` SHALL include the backend. Missing or broken optional
dependencies at handoff SHALL fail safely with recovery guidance instead of
silently resuming unbounded set growth. Small profiles SHALL remain usable
without these optional packages.
