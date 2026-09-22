# Synthetic Generation Delta

## ADDED Requirements

### Requirement: Executable Rule Selection And Ordering
Rejected constraints and relationships SHALL neither mutate nor validate rows.
Formula assignments SHALL execute in dependency order; cycles and duplicate
targets SHALL fail with a value-free error.

#### Scenario: Dependent formulas are reversed
- **WHEN** c = b * 2 precedes b = a * 2 in the spec
- **THEN** b is computed before c and both validate.

### Requirement: Nullable Relationships And Complete Field Bounds
Nullable non-primary-key foreign keys SHALL preserve generated nulls and accept
them during validation. Required identifiers SHALL reject missing values.
String-pattern bounds SHALL include the complete generated string.

### Requirement: Valid Publication And Row Privacy
Non-negative generation SHALL validate all schema, relationship, and constraint
invariants regardless of report toggles, before returning or publishing rows.
Row privacy SHALL be checked in every mode and after business-rule mutation.
Standalone validation with privacy enabled SHALL inspect the supplied rows.
Numeric CSV decoding SHALL NOT weaken the strict classification of strings
returned by generation formulas or business-rule callbacks. An active aggregate
mapping without an active relationship SHALL fail validation.

#### Scenario: A rule mutation invalidates an earlier invariant
- **WHEN** final rows fail a required invariant in valid mode
- **THEN** generation fails without publishing or replacing an output bundle.

#### Scenario: Controlled negative generation
- **WHEN** an explicit negative or mixed mode is requested
- **THEN** invalid rows remain available with their validation evidence
- **AND** unsafe row values still prevent publication.
