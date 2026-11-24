# Artifact Contract Delta

## ADDED Requirements

### Requirement: Preserve CSV encoding behavior during optimization

CSV encoding optimizations SHALL preserve the previous output bytes for the
same supported rows and field order. They SHALL retain header/cell formula
neutralization, scalar formatting, quoting, delimiters, record endings, Unicode,
missing/extra field handling, exceptions and input non-mutation. Shared formatting
policy SHALL apply to every source-derived specification without a source-label
bypass.

#### Scenario: A cell or header could be interpreted as a formula

- **GIVEN** fictional string headers or cells contain dangerous prefixes,
  whitespace or control characters
- **WHEN** ordinary or streaming CSV encoding runs
- **THEN** the existing neutralization result is retained
- **AND** CSV quoting and output bytes match the previous implementation.

#### Scenario: Supported scalar and schema edge cases are encoded

- **GIVEN** fictional rows contain supported native/string values, subclasses,
  missing fields or unexpected fields
- **WHEN** CSV encoding evaluates the rows
- **THEN** formatting, column order, schema decisions and exceptions match the
  previous implementation
- **AND** caller-owned rows remain unchanged.

### Requirement: Retain validation and atomic CSV publication

Encoding SHALL retain all mandatory validation/privacy boundaries, finite work
and byte limits, private temporary-file handling and atomic publication.
Streaming SHALL retain bounded tile processing. Encoding changes SHALL NOT
authorize unchecked rows or alter generation seed algorithms.

#### Scenario: Encoding or output fails

- **GIVEN** an encoding, I/O, worker or budget failure interrupts an export
- **WHEN** the export cannot complete safely
- **THEN** no partial trusted output is published
- **AND** existing destination protection, private permissions and owned-worker
  cleanup remain enforced.

#### Scenario: Both public CSV paths use a fixed seed

- **GIVEN** eligible ordinary or explicitly enabled streaming generation uses a
  fixed specification, seed and dependency snapshot
- **WHEN** the optimized encoder participates in export
- **THEN** every existing validation and privacy check remains active
- **AND** each engine reproduces its own previous CSV bytes
- **AND** artifact hashes, temporary cleanup and atomic publication are verified.

