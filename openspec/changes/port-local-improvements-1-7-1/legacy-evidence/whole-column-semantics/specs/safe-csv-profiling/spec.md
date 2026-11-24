# Safe CSV Profiling Delta

## ADDED Requirements

### Requirement: Resolve semantics from whole-column evidence

Single-file and folder CSV profiling, including batch helpers and streaming
accumulators, SHALL use one deterministic semantic resolver. It SHALL count
detector outcomes across every nonempty value in the existing profiling pass.
The evidence SHALL contain fixed detector categories and counts only, retain
no additional source values and add no serialized profile field.

Email, phone and SSN content semantics SHALL require at least 80% support among
all nonempty values, compared with integer arithmetic. Insufficient or
conflicting evidence SHALL yield no semantic type. Any recognizable secret
SHALL retain the existing secret priority.

#### Scenario: Rare contact content does not define the whole column

- **GIVEN** a neutral column contains one email, one phone and 98 ordinary values
- **WHEN** profiling resolves semantics
- **THEN** the field has no email or phone semantic
- **AND** changing row order does not change that decision.

#### Scenario: Content reaches the exact semantic threshold

- **GIVEN** 80 of 100 nonempty values support one compatible content semantic
- **WHEN** profiling resolves semantics
- **THEN** that candidate meets the content threshold
- **AND** 79 of 100 values do not meet it.

#### Scenario: Evidence lies after the bounded sample

- **GIVEN** early values and later values support different semantic candidates
- **WHEN** the complete column is profiled
- **THEN** the decision uses all nonempty values
- **AND** the first bounded sample does not determine semantic precedence.

### Requirement: Interpret field names as compatible word-based hints

CSV semantic name inference SHALL split separators and camel case into
case-normalized words. Numeric role evidence SHALL prevent count, amount or
rate names from forcing incompatible contact semantics. Numeric spelling alone
SHALL NOT establish a phone semantic without a compatible explicit phone hint.
An incompatible single name hint and dominant content candidate SHALL resolve
to no semantic. Nonnumeric name/address hints MAY supply semantics when no
sensitive content match exists. All-null fields SHALL NOT gain content semantics.

Resolved CSV semantics SHALL be authoritative for type inference; a substring
fallback SHALL NOT restore a rejected phone or email type.

#### Scenario: A numeric role name contains a contact word

- **GIVEN** numeric counts are named `email_count` or `phoneCount`
- **WHEN** CSV semantics and representation are resolved
- **THEN** they retain numeric representation
- **AND** the name does not force an email or phone semantic.

#### Scenario: A substring resembles a sensitive name word

- **GIVEN** a neutral field name contains `name`, `card` or `phone` only inside
  a larger word rather than as a compatible semantic token
- **WHEN** semantic name hints are resolved
- **THEN** that substring does not establish a semantic type
- **AND** the existing conservative privacy guard remains independent.

### Requirement: Preserve privacy independently of semantic support

Any sensitive content match SHALL continue to mark the field sensitive even
when a semantic candidate fails the dominance threshold. Raw categories and
exact numeric summaries SHALL remain suppressed under the existing policy.
The resolver SHALL NOT weaken shared content detection, conservative name-based
sensitivity, bounded numeric normalization, generated-row privacy, masking or
local-category validation.

#### Scenario: One late secret appears in an otherwise ordinary column

- **GIVEN** an ordinary column has one recognizable secret after its bounded sample
- **WHEN** profiling reads the complete column
- **THEN** secret sensitivity and the existing secret semantic priority apply
- **AND** raw sensitive evidence is not published.

### Requirement: Preserve deterministic semantic decisions and refresh caches

For a fixed multiset of values and field name, semantic/type/sensitivity
decisions SHALL be invariant under row permutations. This requirement SHALL
NOT imply byte-identical full profiles from existing reservoirs or bounded
category and pattern ordering. Generation from the same corrected specification
SHALL remain deterministic with an explicit seed.

The folder profile cache SHALL use format version 7; version 6 and earlier
entries SHALL be treated as misses. Existing saved profiles and plans SHALL
NOT be silently rewritten.

#### Scenario: A matching older cache retains sample-based semantics

- **GIVEN** a matching folder cache has format version 6 or earlier
- **WHEN** the folder workflow requests a profile
- **THEN** the old profile is not reused
- **AND** corrected metadata is recomputed under the existing work budgets.
