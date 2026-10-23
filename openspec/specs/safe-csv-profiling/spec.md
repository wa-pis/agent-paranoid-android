# Safe CSV Profiling Specification

## Purpose

Convert CSV files and CSV folders into safe profile metadata that can drive
synthetic generation without exposing source rows or raw sensitive values.

## Requirements

### Requirement: Profile Metadata Only

CSV profiling SHALL produce metadata, aggregates, distributions, ranges, null
ratios, type hints, relationship candidates, and masked patterns instead of raw
source rows.

#### Scenario: Sensitive values are profiled

- **GIVEN** a CSV contains email, phone, name, address, token, credential, or
  identifier-like columns
- **WHEN** the profiler creates a profile
- **THEN** raw sensitive values are not written to profile artifacts
- **AND** the profile may include only masked patterns or synthetic examples for
  those fields

#### Scenario: Non-sensitive categorical values are profiled

- **GIVEN** a non-sensitive field has a small enum-like distribution
- **WHEN** the profiler creates a profile
- **THEN** the profile may include bounded value counts for generation guidance
- **AND** rare free-text values are not treated as safe examples by default

### Requirement: CSV Structure Detection

CSV profiling SHALL detect practical CSV structure before reading records.

#### Scenario: CSV has a delimiter and header

- **GIVEN** a CSV uses comma, semicolon, tab, or pipe delimiters
- **WHEN** the profiler reads the file
- **THEN** it detects the dialect where practical
- **AND** it rejects missing, blank, or duplicate headers

#### Scenario: CSV has mixed encodings

- **GIVEN** a CSV is encoded as UTF-8, UTF-8 with BOM, or another supported
  fallback encoding
- **WHEN** the profiler reads the file
- **THEN** it selects a readable encoding
- **AND** profile artifacts record safe metadata rather than raw file content

### Requirement: Streaming First

CSV folder profiling SHALL process large files without requiring all source rows
to be held in memory.

#### Scenario: Large folder is profiled

- **GIVEN** a folder contains multiple CSV tables
- **WHEN** the profiler builds a dataset profile
- **THEN** schema, null ratios, distinct estimates, type hints, and safe
  distributions are computed in a streaming pass
- **AND** row-level rule mining uses a bounded sample controlled by
  `--rule-sample-rows`

### Requirement: Safe Cache Contents

Profile caches SHALL contain only safe profile metadata.

#### Scenario: Cached profile is reused

- **GIVEN** a CSV folder profile cache exists for matching file names, sizes,
  modification times, and rule sample settings
- **WHEN** the profiler reuses the cache
- **THEN** the cache contains no source rows or raw PII
- **AND** stale or incomplete cache entries are treated as misses

### Requirement: Bounded Parquet Distinctness Evidence

Parquet profiling SHALL reuse its bounded scalar sensitivity scan to compute
non-null distinctness evidence, retaining at most 10,000 private SHA-256 scalar
digests per column. Digests and source values SHALL NOT appear in artifacts,
provider summaries, diagnostics or audit output. Existing input, cell, expanded
byte and deadline limits SHALL continue to apply to the complete scan.

#### Scenario: Complete supported scalar evidence fits the cap
- **WHEN** every row is inspected and the distinct digest set fits the cap
- **THEN** unique_ratio is the distinct count divided by inspected non-null count
- **AND** unique_ratio_kind is exact, with zero for an empty non-null population

#### Scenario: Distinctness exceeds the cap
- **WHEN** a further distinct scalar is encountered beyond the cap
- **THEN** the retained distinct count yields only a lower_bound ratio
- **AND** it does not certify a primary key, pool size or relationship

#### Scenario: Distinct scalar equality is unsupported
- **WHEN** a column contains binary, composite or nonfinite numeric values
- **THEN** its distinctness remains unknown rather than measured zero

#### Scenario: Null statistics are absent or malformed
- **WHEN** row-group null statistics are incomplete, inconsistent or invalid
- **THEN** null_ratio remains unknown and automatic spec inference rejects it
- **AND** independently inspected distinctness does not fabricate null statistics

#### Scenario: Input inspection is incomplete
- **WHEN** inspection fails a budget or observed row count differs from metadata
- **THEN** no trusted partial profile is returned

### Requirement: Bounded Local Category Validation Work

Local category validation SHALL verify field eligibility and positive integer
limits before consuming values. It SHALL retain no more than the configured
category ceiling and reject upon the next item without exhausting an iterable.
Existing sensitivity, uniqueness, scalar, length and free-text rules SHALL apply.

#### Scenario: Too many candidate values are supplied
- **WHEN** the iterable yields a value beyond the configured ceiling
- **THEN** validation rejects without reading further values or truncating a trusted category set
- **AND** the error does not contain source values

#### Scenario: An invalid field or untyped limit is supplied
- **WHEN** field eligibility or the positive-integer limit contract fails
- **THEN** validation rejects before category-value iteration


### Requirement: Reviewed CSV Numeric Replacement

CSV profiling SHALL retain phone sensitivity, masking and source-free metadata
when numeric text resembles a phone. An optional typed `numeric_storage_type`
SHALL describe integer or finite floating storage only when every inspected
non-null value satisfies it; no majority vote or source extrema SHALL authorize
a synthetic numeric replacement.

`infer-spec --decimal-fields` SHALL accept independently authored synthetic
`numeric_measure` DECIMAL ranges for eligible CSV fields. Protected names,
identifiers, primary-key candidates and relationship endpoints SHALL reject.
The declaration SHALL match the field name and use a validated finite bounded
`decimal_range`; it SHALL NOT alter the source profile or authorize copied rows.
Declared SQL/Parquet DECIMAL precision/scale checks SHALL remain unchanged.

#### Scenario: A reviewed measure resembles a phone
- **GIVEN** numeric phone-like text with complete finite storage evidence
- **WHEN** a matching reviewed synthetic numeric_measure range is supplied
- **THEN** the generated spec uses that range and the source profile stays sensitive
- **AND** the profile, provider request and diagnostics contain no source numeric values

#### Scenario: Late sensitive or malformed content
- **WHEN** an otherwise numeric column includes a formatted phone, secret, nonfinite or nonnumeric outlier
- **THEN** incomplete numeric storage evidence does not permit replacement
- **AND** sensitive names and identifiers cannot be overridden by a declaration

#### Scenario: Old ambiguous profile and saved approval
- **WHEN** an old ambiguous profile lacks numeric storage evidence
- **THEN** replacement requires new profiling and folder cache formats before 8 are recomputed
- **AND** changed evidence or synthetic bounds changes the relevant fingerprint and requires new review
- **AND** absent evidence remains omitted so unaffected old profile fingerprints are stable
