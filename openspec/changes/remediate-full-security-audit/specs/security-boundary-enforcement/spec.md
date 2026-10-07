## ADDED Requirements

### Requirement: Sensitive Evidence Is Preserved Across Boundaries
Profiling and advisor services SHALL enforce sensitivity using source lineage and canonical content before retaining statistics, categories or sending provider requests. Local category opt-in SHALL authorize only bounded non-sensitive local enum evidence and SHALL NOT authorize external disclosure.

#### Scenario: Sensitive SQL alias
- **WHEN** a sensitive physical numeric column is aliased to a harmless output name with local-category opt-in
- **THEN** profiling rejects raw category preservation independent of alias

#### Scenario: Sensitive Trino residual
- **WHEN** a rule profile uses a sensitive target or expression/value operand
- **THEN** exact sensitive residual metrics are rejected or suppressed before disclosure

#### Scenario: Canonical numeric identifier
- **WHEN** folder CSV uses exponent notation for a recognizable numeric identifier
- **THEN** no exact identifier extrema or percentiles enter profile/cache artifacts

#### Scenario: Local category reaches provider
- **WHEN** OpenAI advice is requested for locally preserved categories
- **THEN** provider-bound profile/spec/predicates use field-scoped synthetic labels and no original category literal

### Requirement: Cache Reuse Preserves Current Authorization
Profile cache reuse SHALL be bound to the current local-category authorization and SHALL invalidate stale entries when policy cannot be established.

#### Scenario: Revoked category permission
- **WHEN** a prior allowed-category cache is reused without that permission
- **THEN** original category literals and predicates are not returned

### Requirement: Resource Checks Precede Materialization And Publication
Shared services SHALL enforce effective resource limits before dangerous formula operations, decoded dataset retention, audit record parsing and trusted profile publication.

#### Scenario: Formula sequence multiplication
- **WHEN** a short formula requests an excessive sequence or numeric result
- **THEN** evaluation fails within configured work bounds before allocation

#### Scenario: Parquet expansion
- **WHEN** dictionary-encoded data exceeds decoded-byte or cumulative dataset-cell limits
- **THEN** validation rejects before unbounded Python-list materialization

#### Scenario: Expired CSV invocation
- **WHEN** a CSV profiling invocation deadline expires during work
- **THEN** the service fails and publishes no trusted partial profile

#### Scenario: Oversized audit record
- **WHEN** an audit record exceeds its byte limit
- **THEN** the verifier rejects after a bounded read before JSON/HMAC processing

### Requirement: RC Follows Completed Remediation And Fresh Review
An RC SHALL be published only after all validated findings are fixed, the complete final SHA passes fresh full security review and required tests, and original transformation acceptance plus release gates are satisfied.

#### Scenario: Fresh review finds a defect
- **WHEN** fresh full review confirms a security defect
- **THEN** automation returns to remediation and does not publish RC

#### Scenario: Clean review and release gates
- **WHEN** the exact release SHA has clean complete review and all required release/approval/signature/artifact gates pass
- **THEN** automation may publish the unused 1.6.0 RC and verify its public artifacts without publishing stable

### Requirement: Follow-up Allocation Boundaries Are Shared
YAML loaders SHALL bound logical expanded nodes and bytes and reject cycles before construction. Deterministic generation SHALL bound per-value and cumulative allocation for every caller. Folder inference SHALL charge cumulative work and check deadlines within candidate and row loops. Parquet profiling SHALL bound nested logical values before Python conversion.

#### Scenario: Bounded ordinary alias
- **WHEN** YAML reuses a small acyclic mapping within logical limits
- **THEN** ordinary alias semantics remain supported

#### Scenario: Alias amplification
- **WHEN** YAML aliases exceed logical input limits despite a small physical file
- **THEN** parsing rejects before expanded model serialization

#### Scenario: Direct synthesis allocation
- **WHEN** direct generation, SQL export or transformation synthesis requests excessive string allocation
- **THEN** the shared generator rejects before constructing rows

#### Scenario: Combinatorial inference
- **WHEN** folder inference exceeds its deadline or cumulative evaluation allowance
- **THEN** mining stops within its inner loops without trusted profile publication

#### Scenario: Nested profile expansion
- **WHEN** nested Parquet profile content exceeds logical cell or size bounds
- **THEN** inspection rejects before nested Python materialization


### Requirement: Deterministic Rule Work Is Bounded Across Callers
Native constraints and business-rule application/validation SHALL enforce
cumulative work allowances and cooperative deadlines inside their loops.
Generation SHALL reject obvious native rule amplification before row creation.
Negative FK and aggregate estimates SHALL include repeated row scans. Resource
failures SHALL escape formula error reporting and prevent trusted publication.

#### Scenario: Native temporal amplification
- **WHEN** repeated constraints exceed estimated or actual evaluation limits
- **THEN** direct generation/solving/validation reject within bounded work

#### Scenario: Expiry during aggregate validation
- **WHEN** the explicit budget expires inside an aggregate scan
- **THEN** the resource failure propagates instead of becoming a validation result

#### Scenario: Negative cross-table work
- **WHEN** negative generation repeatedly scans parents or aggregate rows
- **THEN** preflight accounts for quadratic work and inner scans consume one shared budget

#### Scenario: Existing callback shape
- **WHEN** a business callback accepts two or three positional arguments
- **THEN** its argument shape remains supported with optional keyword-only budget propagation

### Requirement: PostgreSQL Credentials Require Server Identity Verification
PostgreSQL direct, environment and JDBC configuration SHALL default to `verify-full`. Modes without full server identity verification SHALL require explicit existing local insecure opt-in before resolving credentials or connecting. Connection errors SHALL NOT cause weaker-mode fallback.

#### Scenario: Default remote configuration
- **WHEN** no TLS mode is explicitly selected
- **THEN** the driver receives `verify-full` and operators configure a trusted CA and certificate hostname.

#### Scenario: Weak mode without acknowledgement
- **WHEN** direct, environment or JDBC configuration selects `require`, `verify-ca`, or `disable` without local insecure opt-in
- **THEN** configuration fails before password resolution or driver connection.

### Requirement: Ordinary Trino categories are bounded before driver return

Ordinary table profiling SHALL bound the same VARCHAR representation that it
projects before returning category values to the driver. It SHALL preserve
original grouping and counts, and SHALL reject an oversized-value NULL
sentinel before classifying sensitivity or publishing a profile. It SHALL NOT
truncate or filter oversized categories into an apparently complete summary.

#### Scenario: Source category grows after aggregate profiling

- **GIVEN** an authorized low-cardinality fictional string column
- **WHEN** a value exceeds the input-cell character or UTF-8 representation bound
- **THEN** the category query returns a bounded rejection sentinel
- **AND** ordinary profiling fails with a value-free error before publication.

#### Scenario: Bounded categories keep their counts

- **GIVEN** bounded fictional Unicode and empty-string categories
- **WHEN** ordinary Trino table profiling summarizes categories
- **THEN** original grouping counts remain intact and source-free labels or
  sensitive patterns retain the existing classification contract.


### Requirement: Source fingerprints and inventories remain resource bounded

Source fingerprints SHALL charge actual per-file and cumulative read bytes and
check local and captured invocation deadlines before and after each read.
Folder inventories SHALL enumerate incrementally, check deadlines for all
entries, reject the first matching path beyond the configured file count, and
sort only the bounded inventory. Profiling, cache, planning and dataset loading
SHALL share these controls without silently skipping invalid matching inputs.

#### Scenario: Selected source grows after preflight

- **WHEN** a synthetic CSV grows after its size preflight
- **THEN** fingerprinting rejects actual byte or deadline exhaustion before publication
- **AND** stable bounded inputs retain the existing digest framing.

#### Scenario: Oversized or slow folder inventory

- **WHEN** a selected folder exceeds its matching-file count or enumeration deadline
- **THEN** enumeration stops, closes its directory handle, and returns no trusted profile or fingerprint
- **AND** valid bounded folders retain deterministic filename ordering.

### Requirement: Bound generation seed width before allocation
The system SHALL reject seeds outside signed 64-bit integer range before generator setup or row materialization. Persisted DatasetSpec seeds SHALL remain nonnegative and at most 2**63-1. Accepted seeds SHALL retain existing deterministic identifier formulas without truncation or hashing.

#### Scenario: Oversized direct seed
- **WHEN** a direct generator caller supplies a seed beyond signed 64-bit range
- **THEN** generation fails with a value-free resource error before Faker setup and no rows are created

#### Scenario: Oversized persisted or overridden seed
- **WHEN** an oversized seed is loaded from DatasetSpec settings or supplied to a bundle workflow
- **THEN** validation rejects it before output publication

#### Scenario: Compatible bounded seed
- **WHEN** generation uses an accepted seed, including a negative direct Python seed
- **THEN** identifiers retain their existing formula and repeated generation is deterministic

### Requirement: Saved profile recapture allocation
The system SHALL bound each external saved-profile recapture to the byte length
of its immutable admitted payload before allocation and SHALL reject changed
bytes before publishing a profile.

#### Scenario: Source grows after admission
- **WHEN** a source grows after batch capture while remaining below the aggregate budget
- **THEN** saving the batch rejects growth before reading the source payload
- **AND** no saved profile is published

### Requirement: Cleanup warning transport
The system SHALL preserve a value-free cleanup-incomplete warning across common
CLI and MCP error boundaries when retained artifact removal is unconfirmed.

#### Scenario: Publication and rollback fail
- **WHEN** publication fails and rollback cannot confirm artifact removal
- **THEN** the operator receives a warning that output or staging may remain
- **AND** the warning requests destination inspection before retrying without private cause details

### Requirement: CSV row width enforcement
The shared CSV dictionary reader SHALL reject surplus fields before returning
a row to dataset loading, single-file profiling, snapshot profiling or folder profiling.

#### Scenario: Narrow header with surplus cells
- **WHEN** a CSV row contains more fields than its header
- **THEN** a value-free input-limit error rejects the row before retention
- **AND** existing missing-field padding remains supported

### Requirement: Typed provider-bound distribution metadata

Imported field profiles and specifications SHALL reject nonempty distribution
objects without a supported string kind at their shared model boundary. Empty
metadata SHALL remain valid. Provider adapters SHALL revalidate the request
before transport, including profile and baseline specification mutations.

#### Scenario: Opaque distribution contains synthetic source markers
- **WHEN** imported or mutated metadata contains an unsupported or missing kind
  and nested fictional source markers
- **THEN** validation refuses before any provider SDK request
- **AND** rendered errors do not contain the rejected marker values.
