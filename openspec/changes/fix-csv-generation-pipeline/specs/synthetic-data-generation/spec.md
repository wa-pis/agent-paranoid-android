## ADDED Requirements

### Requirement: CSV round trips preserve safe generation semantics
CSV profiling and inference SHALL produce deterministic valid synthetic data
for bounded categorical IDs, decimal amounts and long entity names.

#### Scenario: Financial CSV with repeated snapshot identifiers
- **WHEN** a synthetic CSV has 2,000 unique row identifiers, two snapshot IDs,
  decimal amounts and a long entity name
- **THEN** generated row identifiers are unique and pass privacy validation
- **AND** snapshot IDs retain two synthetic categories
- **AND** decimal amounts remain numeric without phone classification

### Requirement: Bounded distinct evidence does not assert false uniqueness
CSV profiles SHALL count distinct fingerprints within their resource budget
and SHALL NOT certify uniqueness after that budget is exhausted.

#### Scenario: Duplicates beyond the frequency tracking budget
- **WHEN** 2,000 rows contain 1,400 distinct identifiers
- **THEN** the field is not a primary-key candidate

### Requirement: Reviewed local CSV enums remain checked
Explicitly allowlisted CSV string categories SHALL pass the existing bounded
non-sensitive category validation before literal values are retained.

#### Scenario: Sensitive opt-in rejected
- **WHEN** a local category request includes sensitive values or identifiers
- **THEN** profiling fails without publishing those values

### Requirement: Spaced timezone offsets preserve timestamp precision
CSV timestamp parsing SHALL preserve the time and UTC offset when separated
by whitespace.

#### Scenario: Timestamp with compact spaced UTC offset
- **WHEN** a value is `2026-07-22 19:49:46.000 +0300`
- **THEN** the profile reports a datetime range with offset `+03:00`
