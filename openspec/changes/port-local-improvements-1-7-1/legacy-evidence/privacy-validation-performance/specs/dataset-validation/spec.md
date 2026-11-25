# Dataset Validation Delta

## ADDED Requirements

### Requirement: Prepare row privacy field metadata locally

Row privacy validation SHALL prepare effective field metadata and sensitivity
once per entity and invocation. Preparation SHALL preserve field order, existing
sensitivity policy, value classification and synthetic namespace decisions.
Prepared metadata and row verdicts SHALL NOT be cached across calls or mutations.

#### Scenario: A specification changes between validation calls

- **GIVEN** a previous validation completed successfully
- **WHEN** a field name, type, semantic type or sensitivity flag changes
- **THEN** the next call prepares metadata from the edited specification
- **AND** no previous plan or row verdict authorizes the current rows.

### Requirement: Preserve strict privacy while omitting redundant scalar work

Row privacy validation MAY omit content classification for actual non-string
scalars only after retaining existing blank and composite checks. Nonempty string
values SHALL retain the existing detector and synthetic namespace policy.
Mandatory generated-row checks SHALL remain independent of report settings and
SHALL NOT apply report-only numeric-string decoding.

#### Scenario: A composite appears in a generated field

- **GIVEN** a row contains a dictionary, list or tuple as a field value
- **WHEN** privacy validation runs in any generation mode
- **THEN** the existing scalar-field error is returned before publication
- **AND** the error contains no failing value.

#### Scenario: A declared numeric field contains a sensitive-looking string

- **GIVEN** a string would fail the existing strict generated-value privacy policy
- **WHEN** its field is declared numeric or report sections are disabled
- **THEN** mandatory checks still apply the unchanged string detector and policy
- **AND** report numeric decoding does not authorize generated output.

#### Scenario: An ordinary scalar is not a string

- **GIVEN** an actual non-string scalar passed the existing blank/composite checks
- **WHEN** privacy validation skips its string-only content classifier
- **THEN** the privacy decision is identical to the existing policy
- **AND** schema and other mandatory checks retain their existing boundaries.
