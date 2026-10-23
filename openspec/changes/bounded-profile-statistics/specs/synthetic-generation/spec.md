## ADDED Requirements

### Requirement: Exact Whole-Second Temporal Sampling Bounds

Date and datetime range sampling SHALL compute the admissible whole-second
span without floating-point duration rounding. Generated samples SHALL remain
within the supplied temporal endpoints, including long fractional intervals
and compatible timezone offsets. Existing whole-second sampling and fallback
endpoint values SHALL remain unchanged. An effective interval whose fallback
endpoint conflicts with a supplied bound SHALL reject before publication.

#### Scenario: A long interval has a fractional upper endpoint
- **GIVEN** valid reviewed datetime endpoints separated by many centuries
- **WHEN** sampling selects the largest admissible whole-second offset
- **THEN** the result does not exceed the supplied upper endpoint
- **AND** the result retains the lower endpoint's microsecond and timezone basis

#### Scenario: A subsecond interval contains no further whole-second offset
- **WHEN** the positive interval is shorter than one second
- **THEN** sampling returns the lower endpoint without inventing finer precision

#### Scenario: A supplied partial bound conflicts with the default endpoint
- **WHEN** applying the existing missing-bound defaults yields minimum greater than maximum
- **THEN** generation rejects with a value-free recovery hint to supply ordered explicit bounds
- **AND** no previous dataset or manifest is replaced
