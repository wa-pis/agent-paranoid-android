# selective-source-transformation Specification

## Purpose
Specify the authority, formats, limits and output guarantees of registered
mixed-origin transformation. This contract grants no dataset access.

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

### Requirement: Read-only transformation review parity

CLI and generator MCP SHALL prepare the same value-free review and exact-byte
snapshot identity for a saved local behavior policy and supported source
snapshot. MCP SHALL enforce workspace paths and existing input, review and
transport budgets, write no artifacts and mint no approval receipt.

#### Scenario: Agent reviews a saved policy

- **GIVEN** a fictional source snapshot and saved policy inside the workspace
- **WHEN** `review_transformation` is called
- **THEN** its review and snapshot digest equal CLI `transform-review`
- **AND** no source/mapping values, database access, execution or approval occur

#### Scenario: A review path escapes the workspace

- **WHEN** source or policy paths resolve outside the configured workspace
- **THEN** the tool rejects before reading those files
- **AND** existing review and preservation gates remain in force

### Requirement: Input and output formats are independent

The transformation system SHALL support CSV and Parquet file inputs and
separately authorized bounded read-only Trino or PostgreSQL query-result
inputs. Each input SHALL independently support CSV, Parquet and PostgreSQL SQL-script
file outputs through shared transformation and validation semantics. Adapters
SHALL own physical encodings while the common core owns field policy and
logical types. Approval SHALL bind the captured source and selected output
settings as well as the policy and mappings. SQL outputs SHALL NOT execute
database writes. SQL-file input is outside this requirement.

#### Scenario: Cross-format transformation

- **GIVEN** a fictional authorized input snapshot and reviewed field policy
- **WHEN** any of the four input kinds selects any of the three output kinds
- **THEN** the same one-to-one field rules and logical validation apply,
  independent of physical encoding, and failed validation publishes no output.
- **AND** null/empty, exact decimal and explicit temporal semantics survive
  supported adapter readback without implicit type coercion.

#### Scenario: Database query result exported as a script

- **GIVEN** an authorized bounded read-only Trino or PostgreSQL result snapshot
- **WHEN** SQL-script output is selected
- **THEN** the system creates a PostgreSQL script file using safe
  literal/identifier encoding, never executes it, and preserves source access
  allowlists, budgets and sensitivity gates.

### Requirement: Exact-text CSV replacement scopes

The separate `replace_text` action SHALL support an exact-text CSV table for
the whole single-file policy and optional tables for individual columns at
the same time. Matching SHALL use original decoded cell text once, without
type inference, coercion, trimming or cascade. File-wide rules SHALL apply
only to fields explicitly assigned `replace_text`, not override other field
actions. An unmapped cell SHALL fail unless a separately authorized fallback
is declared. A matching column key SHALL take precedence over a matching
file-wide key; otherwise the file-wide match, then declared fallback SHALL
apply. Duplicate keys within one table SHALL fail. Local trace SHALL be bounded
and value-free and report the same selected rule as execution.

#### Scenario: Column override does not cascade

- **GIVEN** fictional rules `a → b` file-wide and `a → c` for one column,
  and an additional file-wide `c → d` rule
- **WHEN** the original cell in that column is `a`
- **THEN** the result is `c`, not `b` or `d`, using the column rule once.
- **AND** another `replace_text` column without that override uses `b`.

#### Scenario: Combined global and column rules

- **GIVEN** a file-wide `true → false` rule and a distinct column-scoped
  `001 → 1` rule on a fictional CSV
- **WHEN** a reviewed transformation is evaluated
- **THEN** both scopes are considered in one pass over original cell text,
  unchanged input is not silently copied and no replacement is cascaded.
- **AND** local debugging reports only row/column/scope/rule ordinals, match
  status and bounded counts, never either literal or its hash.

#### Scenario: One mapping contract regardless of sensitivity

- **GIVEN** a sensitive field and a reachable replacement equal to an original
  value in a sensitive or unresolved field of the same fixed CSV snapshot
- **WHEN** local review or receipt verification runs for explicit replacement
- **THEN** source membership alone SHALL NOT reject the mapping, including an
  explicit permutation of sensitive values.
- **AND** effective sensitivity SHALL remain a value-free field note.
- **AND** direct preserve and preserve fallback SHALL retain their existing
  non-sensitive classification and local human receipt requirements.

#### Scenario: Explicit mapping versus synthesis at output normalization

- **GIVEN** fictional email-shaped explicit replacements and cells without an
  actually applied mapping
- **WHEN** CSV, SQL-script or Parquet output is encoded
- **THEN** only actually mapped cells use the uniform replacement contract.
- **AND** synthesis and preservation retain their existing content
  checks; absent or malformed execution evidence SHALL NOT grant an exception.
- **AND** type, null, snapshot, budget and value-free transport checks remain.

### Requirement: Bounded normalized Parquet encoding batches
The system SHALL encode typed transformation Parquet output in batches of at
most 1024 normalized rows without retaining a second complete normalized dataset.
It SHALL preserve declared scalar types, source-row reuse/cardinality checks,
output byte/time limits, and the single explicit timestamp-offset requirement.
Existing captured input/result storage and native Arrow allocations remain
subject to their existing contracts; this is not a peak-RSS guarantee.

#### Scenario: Late source mismatch after full encoding batches
- **WHEN** the source iterator contains a surplus row after two full batches
- **THEN** encoding fails without returning a publishable Parquet payload

#### Scenario: Timestamp offset appears after a null batch
- **WHEN** the first 1024 timestamp values are null and a later value has an explicit offset
- **THEN** the declared timestamp schema retains that offset
- **AND** any different offset anywhere in the dataset causes failure

### Requirement: Registered field actions and typed mappings

Every source field SHALL have an explicit supported action: `preserve`,
`synthesize`, `substitute`, `replace_text` or `drop`. Private `derive` SHALL NOT be an executable
registered action. Typed substitutions SHALL apply once to original logical
values within the declared field or shared domain. Duplicate keys and
identity mappings SHALL be rejected. Unmapped cells SHALL fail unless an
explicit compatible fallback is declared. Mapping literals SHALL stay local
and outside reviews, responses, logs and reports.

#### Scenario: Typed mapping is selected in a saved policy

- **WHEN** an exact reviewed policy selects a supported typed substitution
- **THEN** repeated equal input keys in its mapping domain use the same replacement
- **AND** row order and row cardinality are preserved
- **AND** undeclared dependencies are not claimed as preserved.

#### Scenario: Unmapped cell requests preservation

- **WHEN** an explicit fallback would retain a source value
- **THEN** the existing sensitivity and matching local receipt gates apply
- **AND** calling it a replacement does not grant preservation authority.

### Requirement: Transformation limits and configured scale acceptance

Transformation SHALL support configured fictional acceptance at 1,000,000
rows and 100 columns under finite explicit budgets. Row, column, cell, byte
and time ceilings SHALL remain independently enforced; no fixture result
implies arbitrary-width input, a fixed throughput or a peak-memory guarantee.
A run cap SHALL NOT exceed the effective deployment or saved-policy ceiling.
The applicable input, review, decoded-format, capture and output limits SHALL
remain distinct from source-free profiling disclosure limits.

#### Scenario: A finite run selects a supported format

- **GIVEN** a fictional target workload and explicit adequate ceilings
- **WHEN** registered transformation completes
- **THEN** required rows and columns are handled without truncation
- **AND** ordered readback, aggregate provenance and cleanup are checked.

#### Scenario: Requested or observed use exceeds the effective budget

- **WHEN** a request exceeds a ceiling or processing exhausts an admitted cap
- **THEN** the safe failure distinguishes rejection from exhaustion with the
  applicable dimension, usage, limit and configuration origin
- **AND** it does not increase a limit, disclose data or publish a partial result.

### Requirement: Validated output and executed cell provenance

Transformation SHALL label its output mixed origin. It SHALL validate before
publication and report aggregate replacement, synthetic and original counts
from actual actions independently of equality with source values. Drops SHALL
be excluded from output-cell proportions; proportions SHALL be unavailable
when no output cells remain. Conformance SHALL NOT be represented as proof of
fidelity or anonymity.

#### Scenario: Execution is refused before publication

- **WHEN** the snapshot digest differs, an output cap is exhausted, validation
  fails or the destination already exists
- **THEN** no new output is published, and source and existing destination stay unchanged
- **AND** errors disclose no source or mapping values
- **AND** unverifiable staging cleanup uses its distinct sanitized error.
