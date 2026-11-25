# Safe Profile Inference Delta

## ADDED Requirements

### Requirement: Retain signal reasons without changing privacy classification

Shared content classification SHALL retain a fixed reason for each recognized
signal without retaining source values. Its legacy type classifier SHALL
preserve the previous tags, regex/helper behavior, priority and exceptions.
Semantic evidence SHALL use fixed signal counters without adding serialized
profile fields or per-value evidence collections.

#### Scenario: Strict safety consumes a weak signal

- **GIVEN** a value has a weak SSN, card, entropy or JWT-shape signal
- **WHEN** a strict privacy, masking or local-category consumer classifies it
- **THEN** its prior sensitive type result and safety decision are preserved
- **AND** semantic uncertainty does not authorize disclosure.

### Requirement: Require context before weak signals establish semantics

Bare and partially hyphenated SSN shapes SHALL require compatible SSN or
`tax_id` name context to establish SSN semantics. Luhn matches SHALL require
compatible complete-word card, `cc` or PAN context to establish secret semantics.
Entropy and JWT shapes SHALL require compatible credential context, such as
secret, token, password, credential or an explicit supported key phrase.
Generic key, identifier or hash names SHALL NOT provide that context.

Each contextual candidate SHALL account for at least 80% of nonempty values
using integer counts. Structured SSN shapes with both expected ASCII hyphens
MAY establish SSN semantics at that same threshold without an explicit name
hint, subject to existing conflict handling. Known credential formats, private
key markers, explicit Bearer values and secret assignments SHALL retain strong
secret priority even when rare.

#### Scenario: A neutral numeric identifier resembles an SSN

- **GIVEN** a neutral numeric column contains bare nine-digit SSN-shaped values
- **WHEN** the resolver evaluates its weak signal without SSN context
- **THEN** the column has no SSN semantic
- **AND** its sensitive flag and summary suppression remain enabled.

#### Scenario: A possible card has compatible context

- **GIVEN** at least 80% of nonempty values pass the existing Luhn detector
- **AND** the field has a compatible complete-word card name hint
- **WHEN** the resolver evaluates the column
- **THEN** it may assign the existing `secret` semantic
- **AND** the same values in a neutral identifier field do not establish it.

#### Scenario: An opaque identifier has high entropy

- **GIVEN** a neutral hash or identifier field contains high-entropy strings
- **WHEN** the resolver has no compatible credential context
- **THEN** it leaves the semantic unknown
- **AND** it still treats the recognized content as sensitive.

#### Scenario: A rare strong credential format appears

- **GIVEN** an otherwise ordinary column contains one known credential format
- **WHEN** profiling reads the complete column
- **THEN** strong secret priority applies independently of the 80% threshold
- **AND** raw sensitive evidence is not published.

### Requirement: Preserve weak risk through numeric representations and masks

Both CSV paths SHALL retain signal reasons discovered through the existing
bounded canonical and retained-float numeric normalization. Strength handling
SHALL NOT change existing numeric-content exemptions or strict type-tag priority.
Uncorroborated weak evidence SHALL retain sensitivity and suppress raw categories
and exact numeric summaries. Its masked presentation SHALL use generic lengths
rather than an unsupported SSN or secret semantic claim.

#### Scenario: Exponent notation hides a possible payment card

- **GIVEN** permitted bounded numeric normalization reveals a Luhn signal
- **WHEN** a CSV path accumulates that value
- **THEN** its weak card reason remains available to the semantic resolver
- **AND** the original spelling does not bypass privacy suppression.

### Requirement: Apply signal strength to existing weighted aggregate profiles

Trino profile completion and legacy aggregate-profile adaptation SHALL use the
same signal-strength semantic policy for existing top-value evidence. Weighted
support SHALL reuse the available counts without repeating classification per
counted row. This change SHALL NOT add SQL, samples, row-returning access,
database permissions or aggregate artifact fields.

Contextual and threshold-based inference SHALL require strict integer count
metadata and a known strict-integer full non-null population whose size is at
least the observed count sum. Support SHALL be compared with that full population,
not merely the bounded observed subset. Unknown or malformed coverage SHALL
permit only the existing strong-credential priority to establish newly inferred
semantics. Any recognized sensitive signal SHALL retain privacy protection even
when its count or coverage metadata is invalid.

Existing explicit semantic metadata SHALL be preserved. Neither explicit nor
unknown semantics SHALL authorize disclosure of recognized sensitive content.

#### Scenario: A partial top-value list has compatible weak context

- **GIVEN** observed top values contain a weak signal with compatible name context
- **AND** their weighted support is below 80% of the full non-null population
- **WHEN** either aggregate adapter infers semantics
- **THEN** the observed subset does not establish that semantic
- **AND** sensitive evidence remains suppressed.

#### Scenario: Aggregate support reaches the exact threshold

- **GIVEN** validated weighted support is 80 of 100 non-null values
- **AND** its weak signal has compatible context
- **WHEN** either aggregate adapter applies the shared threshold
- **THEN** the candidate meets the support requirement
- **AND** 79 of 100 values do not meet it.

#### Scenario: Counts cannot establish trustworthy coverage

- **GIVEN** an aggregate contains a recognized weak signal
- **AND** count metadata or the full non-null denominator is unknown or malformed
- **WHEN** either adapter completes the profile
- **THEN** it does not infer semantics from weak weighted support
- **AND** invalid metadata does not bypass the signal's privacy protection.

#### Scenario: A saved profile supplies explicit semantic metadata

- **GIVEN** a profile already contains an explicit semantic type
- **WHEN** an adapter evaluates its existing top-value evidence
- **THEN** the explicit type is preserved rather than silently re-inferred
- **AND** sensitive-content checks continue to apply.

### Requirement: Evaluate semantic accuracy independently of privacy caution

An independently labeled synthetic corpus SHALL include positive and hard
negative SSN, card, entropy/JWT and strong-secret cases. Verification SHALL
report semantic precision/recall separately from conservative privacy protection
using aggregate evidence only. Corpus results SHALL NOT be presented as general
real-world accuracy guarantees.

#### Scenario: A sensitive opaque identifier is not a semantic secret

- **GIVEN** a labeled corpus case expects an opaque identifier with unknown semantics
- **AND** the existing conservative detector flags it as sensitive
- **WHEN** accuracy is evaluated
- **THEN** unknown semantics can be a correct semantic result
- **AND** retained sensitivity is assessed separately from semantic false positives.

### Requirement: Preserve deterministic inference and refresh prior caches

Semantic/type/sensitivity decisions SHALL remain invariant under row permutations.
Generation from the same corrected specification SHALL remain deterministic with
an explicit seed. These guarantees SHALL NOT imply byte-identical full profiles
from existing bounded samples or category/pattern ordering.

The folder cache SHALL use format version 8 and reject version 7 and earlier
entries. Saved profiles and plans SHALL NOT be silently rewritten.

#### Scenario: An older profile promoted weak evidence to semantics

- **GIVEN** matching cached source metadata uses format version 7 or earlier
- **WHEN** the folder workflow requests a profile
- **THEN** the older entry is treated as a miss
- **AND** corrected inference is recomputed under existing work budgets.
