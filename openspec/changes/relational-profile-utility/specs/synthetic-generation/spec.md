## ADDED Requirements

### Requirement: Reviewable Relational Utility Evidence

Relational planning SHALL distinguish observed facts, unreviewed hypotheses and
approved executable relationships. Unknown fidelity SHALL NOT be reported as a
successful source-fidelity check.

#### Scenario: No logical relationship has been declared
- **WHEN** generation validates an otherwise valid specification without edges
- **THEN** relationship coverage is untested rather than measured perfect integrity
- **AND** any inferred candidate requires review before execution

#### Scenario: Parent and child sizes differ
- **GIVEN** reviewed counts and an approved foreign key
- **WHEN** data is generated with a fixed seed
- **THEN** non-null child references resolve to generated parent keys
- **AND** independent identifier domains do not collide by row position

#### Scenario: Composite primary-key metadata is received
- **WHEN** the planner cannot represent the complete key
- **THEN** it reports the unsupported structure without certifying one component as unique

#### Scenario: Declared scalar primary key has no identifier suffix
- **GIVEN** authorized PostgreSQL metadata declares a single INTEGER or STRING primary key
- **WHEN** a profile is inferred into a generation specification
- **THEN** the key is a synthetic identifier regardless of its name
- **AND** its type and sensitivity classification are retained
- **AND** seeded generation produces unique synthetic keys without fetching source keys

#### Scenario: Only part of a composite primary key is authorized
- **GIVEN** the column allowlist exposes one component of a composite primary key
- **WHEN** PostgreSQL profiling reads bounded catalog metadata
- **THEN** the complete key arity causes an explicit unsupported-key rejection before aggregate scans
- **AND** no unauthorized component name or source key value is returned

#### Scenario: Declared scalar key has an unsupported generation type
- **WHEN** a declared PostgreSQL primary key has a type other than INTEGER or STRING
- **THEN** profiling requests a reviewed generation specification instead of inferring incompatible synthetic identifiers

#### Scenario: Repeated identifier count is available
- **GIVEN** a supported adapter profiles a repeated identifier with an available positive distinct count
- **WHEN** a reviewed specification requests more generated rows
- **THEN** the existing synthetic pool size is retained through adapter normalization and specification serialization
- **AND** generation is deterministic without source keys or source row mappings
- **AND** an approximate source count does not become a claim of exact source cardinality

#### Scenario: Distinctness evidence is unavailable or censored
- **GIVEN** a Parquet profile with unknown distinctness or a CSV profile whose distinct tracker is censored or overflowed
- **WHEN** synthetic generation is planned
- **THEN** no fixed pool is inferred from that unavailable or censored evidence
- **AND** it cannot certify a primary key

#### Scenario: A reviewed plan requests unequal entity sizes
- **GIVEN** a profile and explicit positive per-entity row counts
- **WHEN** inference resolves requested sizes
- **THEN** exact-name overrides take precedence over the existing global count
- **AND** unspecified entities retain the global or profile-based count
- **AND** neither profile metadata nor source key values are modified
- **AND** declared relationships still bind independently generated keys

#### Scenario: A planning ceiling rejects an oversized specification
- **GIVEN** an explicit positive total-row planning ceiling
- **WHEN** resolved entity counts exceed it
- **THEN** inference rejects before field inference and specification publication
- **AND** the ceiling is not represented as a persisted runtime guarantee
- **AND** later generation count overrides or load multiplication require renewed size review

#### Scenario: Entity sizing input is ambiguous or invalid
- **WHEN** a CLI override repeats an entity, refers to an unknown entity or supplies a nonpositive/noninteger count
- **THEN** inference rejects without publishing a spec or reflecting rejected values

#### Scenario: Saved metadata supplies relationship hypotheses for review
- **GIVEN** a saved profile containing authorized entity and field metadata
- **WHEN** relationship discovery exports a candidate report
- **THEN** the report binds candidates to the profile fingerprint and marks human review required
- **AND** no source values, database/provider queries or generation authority are introduced
- **AND** only entities and fields already in the profile may be referenced

#### Scenario: Names and counts do not establish key-domain identity
- **GIVEN** same-named compatible fields, possibly with competing parents or different underlying domains
- **WHEN** metadata-only discovery produces candidates
- **THEN** domain overlap and source integrity remain explicitly untested
- **AND** accepting a discovery proposal does not modify the generation specification
- **AND** absent parent tables are not looked up or invented

#### Scenario: Discovery exceeds its bounded allowance
- **WHEN** metadata mining exceeds its shared work/deadline allowance, 1,000-candidate cap or report byte ceiling
- **THEN** discovery fails without publishing a partial trusted report

#### Scenario: Empty supplied relations are validated
- **WHEN** direct or CLI validation receives empty parent or child tables
- **THEN** no references yields an unknown resolution ratio, while a real orphan fails
- **AND** nullable child references do not require an invented parent
- **AND** positive declared row counts still reject empty output as a schema mismatch
- **AND** validation leaves supplied files unchanged

### Requirement: Unequal Relational Sizes Have Executable Acceptance

Seeded generation SHALL preserve declared unequal entity counts and nullable
foreign-key behavior consistently through direct and CLI entry points.

#### Scenario: Parent and child counts differ with nullable keys
- **WHEN** reviewed parent and child sizes differ and child keys are all null or all non-null
- **THEN** direct and CLI seeded runs have identical rows and exact declared counts
- **AND** non-null child references resolve to generated parent keys
- **AND** independent identifier domains remain disjoint and input specs remain unchanged

#### Scenario: Supplied relations are empty
- **WHEN** direct or CLI validation receives empty parent or child relations
- **THEN** relationship metrics distinguish no references from a real orphan
- **AND** schema validation still rejects mismatch with positive declared row counts
- **AND** validation does not mutate supplied files
