# Dataset Validation Delta

## ADDED Requirements

### Requirement: Preserve privacy recognition when guarding detector dispatch

Shared content classification MAY omit a regular-expression call only when a
necessary-match condition proves that the existing expression cannot match.
Classification SHALL retain the original patterns, flags, Unicode behavior,
stripping, date exclusion, scalar handling and recognition priority. Entropy
checks SHALL retain their original alphabet, character classes, ordered counts,
mathematical operations and threshold. Dispatch optimization SHALL NOT cache
values or decisions, retain raw inputs, or consume randomness.
Necessary-character tests SHALL inspect the underlying string content used by
the regular expressions, independently of overridden string membership methods.

#### Scenario: A required assignment separator is absent

- **GIVEN** stripped text contains neither `:` nor `=`
- **WHEN** classification omits the existing secret-assignment search
- **THEN** its result equals the original classifier's result
- **AND** every other detector retains its existing input and priority.

#### Scenario: A possible assignment includes Unicode or embedded text

- **GIVEN** stripped text contains a possible assignment with `:` or `=`
- **WHEN** classification evaluates that assignment
- **THEN** the original case-insensitive expression searches the unchanged text
- **AND** Unicode, whitespace, search scope and newline behavior stay unchanged.

#### Scenario: An email match cannot contain its required character

- **GIVEN** stripped text contains no `@`
- **WHEN** classification omits the existing email full match
- **THEN** its result equals the original classifier's result.

#### Scenario: Multiple detectors could recognize a value

- **GIVEN** text contains `@` and also matches a higher-priority secret detector
- **WHEN** the shared classifier runs
- **THEN** the existing secret classification retains precedence over email.

#### Scenario: A string subclass hides required characters from membership

- **GIVEN** a string subclass returns itself from `strip` and overrides
  `__contains__` to hide a literal required by an existing matching expression
- **WHEN** guarded detector dispatch checks that literal
- **THEN** built-in string membership observes the underlying string content
- **AND** the original expression runs and preserves the original classification.

### Requirement: Preserve shared privacy consumers and policy boundaries

Detector dispatch optimization SHALL preserve decisions in generated-row
privacy, CSV and schema profiling, Trino masking, local-category checks,
semantic-provider validation and business-rule contracts. Mandatory checks SHALL
continue to classify raw strings independently of report settings and declared
numeric types. Existing report-only numeric decoding and synthetic namespace
policies SHALL remain unchanged.

#### Scenario: A raw numeric string requires strict privacy checking

- **GIVEN** a generated string fails the existing strict privacy policy
- **WHEN** the field is declared numeric or privacy report sections are disabled
- **THEN** mandatory privacy still rejects it before output publication
- **AND** report-only numeric decoding does not authorize the raw generated value.

#### Scenario: A consumer uses recognizable-sensitive-value classification

- **GIVEN** a profiling, masking, category, provider or rule consumer calls the
  shared classifier
- **WHEN** guarded detector dispatch is enabled
- **THEN** its classification and resulting policy decision equal the original
- **AND** failures and metadata do not expose raw sensitive values.
