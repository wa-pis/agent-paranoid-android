# Safe Source Profiling Delta

## ADDED Requirements

### Requirement: Apply safety independently of source provenance labels

Every source adapter and typed profile safety gate SHALL use the shared
sensitive-data policy. Known, absent or custom `source_type` labels SHALL NOT
authorize exact sensitive numeric summaries or raw sensitive categories.
Legacy normalization SHALL retain safe masked patterns, numeric shape and
synthetic identifiers while suppressing unsafe source summaries. A nested
numeric-shape payload SHALL NOT replace its fixed distribution discriminator.

#### Scenario: A caller changes a profile source label

- **GIVEN** a profile contains exact sensitive numeric summaries
- **WHEN** its source label changes from a database label to a file or custom label
- **THEN** the shared safety gate still rejects it without echoing summary values.

### Requirement: Screen available source scalars without declassifying uncertainty

Accepted source-category scalars and existing numeric-summary evidence SHALL
use bounded canonical numeric risk checks in addition to applicable raw-string
protection. Recognized weak risk SHALL preserve sensitivity even when semantics
is unknown. Numeric extrema alone SHALL NOT establish whole-column semantics.
Strict generated-row classification and the original raw-value classifier SHALL
retain their existing behavior. Explicit reviewed specification numeric scaling
SHALL retain its separate safety contract.

#### Scenario: A numeric category resembles a sensitive identifier

- **GIVEN** an accepted integer source category has recognized sensitive shape
- **WHEN** an adapter or local-category guard examines it
- **THEN** its native numeric type does not authorize raw category preservation
- **AND** an unknown semantic type does not declassify it.

### Requirement: Preserve conservative name risk and SQL projection provenance

Name-risk handling SHALL preserve all earlier positive sensitivity decisions
and recognize the supported complete words and credential/tax key phrases.
SQL projection sensitivity SHALL include both output-name risk and sensitive
physical inputs, including aliases and supported expressions. Unsafe local
category outputs SHALL be rejected before their value query. Newly profiled
query sources SHALL use policy version `1.1` in their metadata and fingerprint.

#### Scenario: A sensitive input is projected under a neutral alias

- **GIVEN** a validated query renames a sensitive physical input
- **WHEN** the profile evaluates the projected output or a local-category request
- **THEN** the sensitive provenance remains protected
- **AND** the alias does not authorize value preservation or exact summaries.

### Requirement: Use existing authorized evidence without adding source rows

Adapters SHALL forward available validated exact non-null counts to the shared
weighted semantic policy. Missing, malformed or rounded coverage SHALL NOT be
treated as full-column evidence. Database parity SHALL use existing authorized
schema/aggregate query families and budgets, without new row-returning access.
Parquet profiling SHALL remain metadata-only and use native Arrow type
predicates; it SHALL NOT read row groups or claim value-level detection.

#### Scenario: A schema-only source lacks content evidence

- **GIVEN** Parquet profiling has only file and schema metadata
- **WHEN** a field has no value-level evidence
- **THEN** the adapter retains its physical type and conservative name risk
- **AND** it does not fetch rows to imitate a complete CSV content profile.

### Requirement: Count all streamed CSV inputs exactly under shared resource bounds

File, byte-snapshot, row-digest and folder CSV profiling SHALL retain complete
distinct counts without a separate unique-value ceiling. Small states SHALL
use sets; states above the shared default of 1,000,000 fingerprints across
fields SHALL hand off through the existing optional DuckDB adapter without
reopening the source. Only field ordinals and one-time keyed digests SHALL
enter its private bounded scratch boundary. Existing input, deadline, native
execution and cleanup requirements SHALL remain enforced.

#### Scenario: A single CSV crosses the in-memory threshold

- **GIVEN** its accumulated distinct state exceeds the shared threshold
- **WHEN** profiling continues through the optional backend
- **THEN** accumulated sets and the remaining iterator produce complete counts
- **AND** no raw values, field names or partial trusted profile are published.

### Requirement: Preserve cardinality evidence and refresh affected caches

New completed single-CSV profiles SHALL mark distinct evidence `exact`; older
payloads without the additive field SHALL default to `unspecified`. Legacy
adaptation SHALL retain the evidence kind. Lower-bound counts SHALL NOT define
fixed identifier pools or nominate primary keys. Historical censored CSV
metadata SHALL NOT gain false exactness, and its former boundary SHALL NOT cap
new exact profiles. Folder cache format 9 SHALL invalidate earlier entries.

#### Scenario: A new exact count exceeds a former single-file boundary

- **GIVEN** complete new profiling marks the count exact
- **WHEN** legacy adaptation considers repeated identifier metadata
- **THEN** the historical 99,999 boundary does not censor the measured count
- **AND** a lower-bound count still cannot create a pool or primary-key candidate.

### Requirement: Keep downstream generation independent of profile origin

Normalized profiles SHALL feed the shared specification, generation, validation
and privacy policy. Explicit eligible streaming specification APIs SHALL work
independently of the original source, retaining seeded replay and atomic output.
Existing source-profile, review/approval and MCP opt-in boundaries SHALL remain;
source parity SHALL NOT automatically enable streaming or broaden source access.
Saved artifacts SHALL NOT be silently rewritten, and historical OpenSpec and
benchmark evidence SHALL remain unchanged.

#### Scenario: Two source adapters produce the same reviewed specification

- **GIVEN** the effective specifications and explicit seeds are identical
- **WHEN** the same generation engine validates and exports them
- **THEN** their source provenance does not change generated results or checks
- **AND** the existing streaming eligibility and approval boundaries still apply.
