## ADDED Requirements

### Requirement: Cross-Interface Acceptance Has Explicit Coverage

Final acceptance of the source/output and MCP work SHALL cover every supported
source, output and mode composition through installed Python, CLI and real stdio
MCP. It SHALL inventory every public option and rule family, test their boundaries
and interactions, and distinguish native interface capabilities from composed
safe-profile/reviewed-specification handoffs.

#### Scenario: A source has no native MCP acquisition tool

- **GIVEN** a supported source can supply a safe profile or reviewed DatasetSpec
- **WHEN** its MCP generation matrix cell executes
- **THEN** the handoff and acquisition interface are recorded explicitly
- **AND** the actual installed MCP tool generates and revalidates the requested output
- **AND** absence of a convenience flag does not excuse missing shared semantics

#### Scenario: An option or tool is added

- **GIVEN** public schemas, parser and discovery contain a new option or tool
- **WHEN** the expected acceptance inventory is reconciled
- **THEN** missing required coverage fails the inventory check
- **AND** compatible pairs, boundaries and relevant high-risk interactions receive cases

#### Scenario: An identifier distribution retains a legacy prefix

- **GIVEN** a reviewed specification includes `synthetic_identifier.prefix`
- **WHEN** synthetic identifiers are generated or the option inventory is reconciled
- **THEN** the property is documented as retained metadata, not a generation control
- **AND** string tokens keep the mandatory `synthetic_` plus ASCII integer namespace
- **AND** the supplied prefix is never copied into generated values

#### Scenario: A tiny exact decimal is exported as CSV

- **GIVEN** a valid reviewed DECIMAL field produces a value represented internally with an exponent
- **WHEN** a typed synthetic CSV bundle is written and independently reloaded
- **THEN** the CSV numeric cell uses exact plain decimal notation
- **AND** standalone validation preserves the declared precision and scale
- **AND** arbitrary exponent-form input strings do not gain new parsing permission
- **AND** formatting rejects unbounded exponents and non-finite values before expanding text

#### Scenario: A signed exact decimal uses the maximum scale

- **GIVEN** a reviewed DECIMAL field declares precision 38 and scale 38
- **WHEN** the smallest or largest fractional magnitude is parsed with either sign
- **THEN** the bounded plain-text parser admits the sign without consuming digit precision
- **AND** out-of-precision, exponent-form and oversized inputs remain rejected

### Requirement: Acceptance Evidence Separates Execution And Authority

Acceptance evidence SHALL bind results to the exact commit, built artifacts and
environment. It SHALL distinguish mocked acquisition, disposable fictional live
databases, automated SDK execution, actual human client review and separately
gated transformation authority. Missing required execution SHALL remain blocked.

#### Scenario: An installation or integration cannot run

- **GIVEN** a required case lacks dependencies, environment or actual execution
- **WHEN** the final report is produced
- **THEN** its status is blocked, not passed or silently skipped
- **AND** N/A is reserved for a documented contract exclusion with its supported
  alternative route where shared generation semantics apply

#### Scenario: A confirmed failure requires a repair

- **GIVEN** the implementation changes after a campaign run
- **WHEN** acceptance is reconsidered
- **THEN** earlier exact-commit acceptance is superseded
- **AND** affected cases and the final full gate run on the final SHA
- **AND** existing independent release and local human approval requirements remain
  separate and cannot be replaced by an automated test result
