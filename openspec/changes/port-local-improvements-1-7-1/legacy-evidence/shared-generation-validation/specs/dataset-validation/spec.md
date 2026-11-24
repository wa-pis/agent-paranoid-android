# Dataset Validation Delta

## ADDED Requirements

### Requirement: Share validation within unchanged CSV candidates

Valid-mode CSV bundle generation without a business-rule applier SHALL share
equivalent mandatory and report checks before writing candidate rows. Public
row-returning generation SHALL continue to enforce mandatory invariants before
return. Shared evaluation SHALL preserve generated rows, seeded output and the
standalone report's sections, effective settings, order and fail-fast behavior.
Validation results SHALL remain local to the current unchanged candidate data;
no persistent validation cache or public bypass SHALL be introduced.

#### Scenario: Produce the existing report without duplicate equivalent checks

- **GIVEN** valid-mode CSV candidates and no business-rule applier
- **WHEN** mandatory enforcement and report construction share evaluation
- **THEN** all mandatory invariants are checked before writing
- **AND** the report equals standalone validation with the same settings
- **AND** candidate values and serialized output remain unchanged.

#### Scenario: Ordinary spec-only CLI generates CSV without rules

- **GIVEN** the unchanged default CLI rule wrapper and no rule file
- **WHEN** a spec-only generate command selects CSV explicitly or through its spec
- **THEN** the known no-op wrapper does not prevent shared validation
- **AND** custom callbacks, rule files and profile-command defaults remain active.

#### Scenario: Report sections are disabled

- **GIVEN** a generated candidate violates a mandatory invariant
- **WHEN** the corresponding report section is disabled
- **THEN** generation fails before encoding or writing that candidate
- **AND** no partial trusted bundle is published.

### Requirement: Preserve privacy policies and mutation boundaries

Shared evaluation SHALL retain strict raw generated-value privacy independently
of declared-type normalization for reports. It SHALL NOT mutate input rows.
Callback workflows, non-valid modes and other output formats SHALL retain their
existing validation path and failure ordering. Mandatory checks SHALL run after
business-rule mutation even when report sections are disabled.

#### Scenario: Numeric decoding would conceal a generated string violation

- **GIVEN** a raw generated string violates mandatory privacy classification
- **WHEN** its declared field type permits numeric report decoding
- **THEN** the raw privacy violation still prevents publication
- **AND** the error does not expose the failing value.

#### Scenario: A business callback mutates previously checked rows

- **GIVEN** generation passed its mandatory checks before a callback
- **WHEN** the callback changes a final row or its effective specification
- **THEN** post-callback mandatory checks evaluate the final state
- **AND** no earlier validation result authorizes invalid or unsafe output.

### Requirement: Reuse validated streaming normalization

Eligible streaming CSV generation SHALL share mandatory/report work within each
tile and reuse normalized rows from that evaluation for global primary-key
checks. It SHALL retain original values for CSV serialization, ordered tile
checks, cross-tile uniqueness, exact final counts, configured budgets and atomic
publication.

#### Scenario: Duplicate normalized keys occur across tiles

- **GIVEN** distinct tiles contain equal normalized primary keys
- **WHEN** global checks consume shared validation's normalized rows
- **THEN** the duplicate fails before complete bundle publication
- **AND** temporary output is cleaned according to the existing policy.
