# RC6 Synthetic Output Safety Delta

## ADDED Requirements

### Requirement: Source Categories Never Become Generated Values

CSV-folder profiling SHALL replace source-derived text categories with
collision-safe synthetic rank labels before a profile is cached, returned, or
used for specification inference and generation. Category counts and inferred
conditional rules SHALL remain consistent after replacement. Numeric
distributions SHALL retain their existing type and magnitude semantics.

#### Scenario: A rare category controls a conditional rule

- **GIVEN** a low-cardinality text field contains source values missed by
  sensitive-value heuristics and one value implies another field is required
- **WHEN** the folder is profiled and synthetic rows are generated
- **THEN** the profile, cache, specification, and rows contain no source text
  category
- **AND** the category counts and conditional requirement use the same
  collision-safe synthetic label
- **AND** generation remains deterministic for an explicit seed

### Requirement: CSV Output Neutralizes Spreadsheet Formula Markers

CSV export SHALL reject or neutralize string cells beginning with spreadsheet
formula markers such as `=`, `+`, `-`, or `@` when the value could be interpreted
as a formula by common spreadsheet applications. This applies to built-in,
advisor, semantic-provider, and constraint-derived values.

#### Scenario: Formula-like generated cell

- **GIVEN** a generated string begins with a spreadsheet formula marker
- **WHEN** CSV output is serialized
- **THEN** the output contains a literal-safe representation
- **AND** JSON, SQL, and Parquet output contracts remain unchanged
- **AND** a validation test proves the CSV cell is not emitted as an executable
  formula token

### Requirement: Semantic Providers Are Bounded And Synthetic-Only

Semantic providers SHALL run behind an enforceable timeout and cancellation
boundary. With an explicit seed, a provider SHALL either support deterministic
replay or return a seed-bound output fingerprint that can be validated. Names,
addresses, and equivalent identity-bearing values SHALL come only from a
synthetic namespace, and generated output SHALL pass privacy and type checks
after provider execution.

#### Scenario: Provider exceeds its execution deadline

- **GIVEN** a semantic provider does not complete before the invocation
  deadline
- **WHEN** generation handles the provider call
- **THEN** the call is cancelled or isolated and fails with a bounded local
  reason
- **AND** no partial provider output is published

#### Scenario: Provider ignores the requested seed

- **GIVEN** the same specification and seed are replayed
- **WHEN** the provider returns output without deterministic replay support
- **THEN** generation rejects the output or records a failed seed-bound
  fingerprint check
- **AND** an identity-bearing source-like value cannot bypass the post-generation
  privacy check

### Requirement: Single-Entity Publication Has A Verifiable Completion Boundary

Single-entity artifact publication SHALL expose an explicit completion or
read-validation boundary. Interrupted publication SHALL not be reported as
complete, and replacing sibling artifacts in a bundle SHALL require explicit
approval rather than silently following staged-name collisions.

#### Scenario: Publication is interrupted

- **GIVEN** a writer stops after replacing only part of a single-entity bundle
- **WHEN** a reader or recovery path inspects the destination
- **THEN** incomplete output is detectable and is not reported as a complete
  bundle
- **AND** recovery does not follow a symlink outside the approved destination
