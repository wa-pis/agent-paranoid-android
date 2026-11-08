# Scalable Relational Generation Delta

## ADDED Requirements

### Requirement: Explicit relational engine and bounded graph admission

The system SHALL accept an explicitly reviewed scalable-relational-v1 policy
for supported acyclic many-to-one/one-to-one relationships targeting generated
synthetic primary keys. It SHALL bound graph traversal and reject unsupported
relationships, modes and rules before staging or worker allocation.

#### Scenario: Parent appears after child in the specification

- **GIVEN** an admitted acyclic graph and unequal entity counts
- **WHEN** the new engine plans execution
- **THEN** it completes parents before children in stable dependency order
- **AND** original entity/field indices still define deterministic streams.

#### Scenario: Unsupported or infeasible graph

- **GIVEN** a cycle, self-link, non-PK target, shared PK/FK or insufficient one-to-one parent domain
- **WHEN** generation is requested
- **THEN** it rejects with a value-free actionable error before creating output
- **AND** it does not silently drop links or switch engines.

### Requirement: Bounded deterministic synthetic foreign keys

The system SHALL generate references solely from synthetic parent key domains,
without source rows or full parent/key pools. The same ordered spec/seed and
environment SHALL yield identical logical data across supported worker/batch
settings. One-to-one assignments SHALL remain unique across batches.

#### Scenario: Chained tables with nullable child keys

- **GIVEN** a supported multi-level graph with nullable foreign keys
- **WHEN** generation uses one, two or four workers
- **THEN** every non-null reference resolves and one-to-one assignments are unique
- **AND** the recorded null mask and distinct child keys are deterministic.

### Requirement: Mandatory relational validation and honest evidence

The system SHALL verify actual FK assignments during generation and streamed
recovery even when optional reports are disabled. It SHALL report executed
relationship checks and actual checked/resolved/null counts without row values.
Parent domain/count/order, hashes and normal privacy/schema checks SHALL remain
mandatory, with finite budgets and no full-table materialization.

#### Scenario: A child artifact contains a wrong foreign key

- **GIVEN** a generated bundle with modified child references and recomputed file hashes
- **WHEN** streamed validation or recovery runs
- **THEN** it rejects invalid synthetic reference assignment
- **AND** it never reports zero relationship checks as successful relational validation.

### Requirement: Atomic bounded dependency-aware execution

The system SHALL share deadlines, memory/output/temp/work budgets across all
parent and child stages and reap workers after failure. Publication SHALL occur
only after all tables pass mandatory checks. Existing independent and legacy
engines SHALL retain their contracts and seeded output.

#### Scenario: A later child fails after a parent finishes

- **GIVEN** completed staged parent output and a failing child task
- **WHEN** execution aborts
- **THEN** no partial dataset replaces the destination and owned staging is removed.

### Requirement: Cross-interface review and measured performance

The new engine SHALL use the existing typed Python/CLI/MCP policy, exact-spec
approval, safe capacity estimates and summary-only responses. Changes to the
engine or relationships SHALL invalidate prior approval. Relational benchmarks
SHALL state actual data shape, worker counts, timings, bytes and memory limits.

#### Scenario: Approved independent plan changes to relational execution

- **GIVEN** prior approval of an independent policy
- **WHEN** engine or relationship declarations change
- **THEN** execution requires review of the changed fingerprint
- **AND** no MCP or AI approval shortcut is introduced.
