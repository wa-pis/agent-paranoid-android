# Dataset Validation Delta

## ADDED Requirements

### Requirement: Avoid redundant normalization metadata work

Normalization SHALL retain structural and scalar eligibility checks before
omitting string-decoding metadata work for actual non-string values. Any
prepared parser/nullability metadata SHALL remain local to one invocation and
SHALL be rebuilt from the current specification on the next call. No conversion
result or mutable specification state SHALL be cached across calls.

#### Scenario: A generated row already contains native scalars

- **GIVEN** a row contains already typed values
- **WHEN** normalization processes it
- **THEN** every value retains the existing scalar eligibility check
- **AND** values requiring no string conversion avoid redundant parser lookup
- **AND** declared field types do not bypass structural or scalar checks.

#### Scenario: A specification changes between calls

- **GIVEN** a previous normalization call completed
- **WHEN** field types, names, nullability or entity definitions change
- **THEN** the next call uses the current specification
- **AND** no prior preparation or result authorizes a current value.

### Requirement: Preserve normalization outcomes and identity

Normalization SHALL preserve the previous numeric/boolean string decoding,
nullable empty-string behavior, unknown-field/entity handling, structural
filtering, exceptions and ordered value-free errors. It SHALL preserve
copy-on-write container and row identities and SHALL NOT mutate input rows or
specifications.

#### Scenario: No conversion or input error occurs

- **GIVEN** a dataset requires no conversion and contains no input errors
- **WHEN** normalization completes
- **THEN** it returns the original dataset object
- **AND** all original row objects remain unchanged.

#### Scenario: Conversion and malformed values coexist

- **GIVEN** fictional input contains decodable strings and malformed structures
  or unsupported scalar values
- **WHEN** normalization completes
- **THEN** decoded values, filtering, ordered errors and exceptions match the
  previous implementation
- **AND** only rows requiring conversion are copied
- **AND** caller-owned values remain unchanged.

### Requirement: Retain shared privacy and deterministic publication

Normalization policy SHALL apply to all supported source-derived specifications
without a source-label bypass. Raw-value privacy SHALL remain separate from
report decoding. Mandatory validation and atomic publication boundaries SHALL
remain unchanged.

#### Scenario: Ordinary or streaming CSV export uses a fixed seed

- **GIVEN** eligible synthetic generation uses a fixed seed
- **WHEN** normalization participates in either public CSV path
- **THEN** each path retains its own previous deterministic output
- **AND** all existing schema, privacy, relationship and constraint checks run
- **AND** artifact hashes, private permissions and temporary cleanup are verified.
