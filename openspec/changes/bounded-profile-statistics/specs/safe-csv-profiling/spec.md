## ADDED Requirements

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
