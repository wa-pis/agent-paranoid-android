## ADDED Requirements

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
