# selective-source-transformation Specification

## Purpose
Specify the authority and accepted scalar relationship semantics of the
registered mixed-origin transformation surface. Remaining capacity and scoped
amendment evidence is tracked separately; this contract grants no dataset access.

## Requirements

### Requirement: Registered transformation is separate from synthetic generation

The reviewed local transformation SHALL require explicit selection, a field
policy and the exact reviewed snapshot. It SHALL produce a labelled mixed-origin
artifact and SHALL NOT supply preservation authority to ordinary generation,
profiling or advisors. Preserving a value or using a preserve fallback SHALL
require an explicitly non-sensitive decision, no positive or conflicting
sensitivity evidence, a bounded operator comment and an exact matching local
controlling-TTY receipt. Unknown or disputed fields SHALL fail closed for
preservation; default DECIMAL preservation remains blocked. MCP SHALL NOT issue receipts or return
source or transformed rows.

Explicit `substitute` and `replace_text` SHALL use deterministic evidence of
actually applied mappings. A mapped replacement MAY equal another source
value, including a sensitive mapped permutation, in the selected local artifact.
Sensitivity notes SHALL remain value-free. This exception SHALL NOT authorize
implicit copying, broaden preservation or permit disclosure in profiles,
review, logs, errors, providers or transport responses.

#### Scenario: Exact snapshot changes after local approval

- **GIVEN** a bound local receipt and an explicitly non-sensitive preserve action
- **WHEN** source, policy, classification, review or referenced input bytes change
- **THEN** execution rejects the earlier receipt before publication.

#### Scenario: Mapped sensitive permutation is not preservation authority

- **GIVEN** an explicit mapping that swaps fictional sensitive values
- **WHEN** the reviewed transformation applies that mapping
- **THEN** only mapped cells follow the replacement contract in the local artifact
- **AND** unmatched preservation still requires its independent authority
- **AND** transport responses remain value-free summaries.

### Requirement: Scalar transformation relationships distinguish null from empty text
Final scalar batch relationship validation SHALL treat only logical `None` as
null. Nullable empty text SHALL participate in parent membership and one-to-one
cardinality checks. Source-free generation validation SHALL retain its existing
empty-string null default through an explicit compatibility option.

#### Scenario: Nullable empty foreign key has no parent
- **GIVEN** a transformed child key is an empty string and the field is nullable
- **WHEN** no parent key equals that empty string
- **THEN** final validation rejects before publication.

#### Scenario: Empty key matches an empty parent
- **WHEN** a transformed empty-string child has an equal parent key
- **THEN** membership passes but duplicate empty children reject one-to-one cardinality.

#### Scenario: Actual null remains nullable
- **WHEN** a transformed nullable child key is logical `None`
- **THEN** it remains exempt from parent membership and one-to-one cardinality.
