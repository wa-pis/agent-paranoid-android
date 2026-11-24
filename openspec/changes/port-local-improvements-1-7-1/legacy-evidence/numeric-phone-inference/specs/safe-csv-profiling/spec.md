# Safe CSV Profiling Delta

## ADDED Requirements

### Requirement: Keep numeric representation independent of weak phone inference

Single-file and folder CSV profiling SHALL preserve numeric representation for
a neutrally named column whose nonempty values all parse as finite numbers
when its only inferred sensitive semantic is phone. Profiling SHALL NOT assign
that column a phone semantic solely from its numeric spelling. Explicit phone
name hints and nonnumeric formatted phones SHALL retain their existing phone
inference. Stronger SSN, payment-card and secret classifications SHALL retain
their existing priority.

#### Scenario: A neutral numeric column resembles phone values

- **GIVEN** all nonempty values of a neutral CSV column parse as finite numbers
- **AND** the only proposed sensitive semantic is phone
- **WHEN** single-file or folder profiling finalizes the field
- **THEN** the field keeps its integer or float representation
- **AND** it has no inferred phone semantic.

#### Scenario: Numeric spelling remains ambiguous sensitive content

- **GIVEN** the content policy flags a numeric column as possibly sensitive
- **WHEN** profiling retains its numeric type without a phone semantic
- **THEN** its sensitive flag remains set
- **AND** exact numeric summaries and raw category values remain suppressed.

#### Scenario: A field has explicit phone evidence

- **GIVEN** a CSV field has an existing phone-name hint or nonnumeric formatted
  phone values
- **WHEN** profiling infers the field's type and semantics
- **THEN** the existing phone classification and masked evidence remain.

#### Scenario: A later value supplies stronger sensitive evidence

- **GIVEN** a CSV field begins with numeric values and has a later recognizable
  SSN, payment-card or secret value outside the bounded semantic sample
- **WHEN** profiling reads the complete field
- **THEN** the stronger content policy is still enforced
- **AND** numeric representation does not authorize raw sensitive evidence.

### Requirement: Use one bounded numeric content policy across CSV profilers

Folder CSV profiling SHALL apply the existing single-file CSV numeric-content
policy, including finite-value checks, bounded numeric normalization, original
and retained-representation detection and the existing negative-fraction
exception. The representation correction SHALL NOT broaden content exemptions
or change strict generated-row privacy, masking or local-category policy.

#### Scenario: A negative fractional measure is profiled through either path

- **GIVEN** a negative non-integral decimal qualifies for the existing CSV
  exception and its retained representation also stays fractional
- **WHEN** single-file and folder profiling classify its content
- **THEN** both apply that same exception
- **AND** no additional exemption is introduced for positive or integral values.

#### Scenario: Numeric normalization reveals stronger sensitive content

- **GIVEN** an allowed original or retained numeric representation reveals
  recognizable sensitive content after the existing bounded normalization
- **WHEN** either CSV profiling path checks the value
- **THEN** the existing sensitive-content decision is retained
- **AND** source spellings do not bypass suppression of unsafe summaries.

### Requirement: Recompute cached profiles after numeric phone inference changes

The folder profile cache SHALL use format version 6. Earlier cache versions
SHALL be treated as misses so corrected numeric type, semantic and sensitivity
metadata is computed again under existing input and work budgets.

#### Scenario: A matching version-5 cache contains false phone inference

- **GIVEN** matching CSV source metadata has an existing version-5 cache entry
- **WHEN** the folder workflow requests a profile
- **THEN** the older entry is not reused
- **AND** corrected safe metadata is written using cache format 6.
