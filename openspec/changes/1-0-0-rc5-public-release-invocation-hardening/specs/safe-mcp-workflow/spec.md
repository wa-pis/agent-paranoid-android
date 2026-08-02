# Safe MCP Workflow Delta

## ADDED Requirements

### Requirement: Public Candidate Artifacts Are Independently Accepted

The release candidate SHALL be accepted only after the exact wheel and sdist,
checksums, SBOM, provenance, and attestations are available from public
artifacts and installable outside the repository checkout.

#### Scenario: Public RC acceptance is run

- **GIVEN** the candidate tag and release metadata identify one commit
- **WHEN** a clean environment installs the public base, `trino`, `mcp`, and
  `mcp,trino` profiles
- **THEN** the installed version, `--version`, `demo`, and `doctor` checks
  succeed for their applicable profiles
- **AND** the README commands run without modification
- **AND** artifact hashes and attestations match the recorded release evidence

### Requirement: Database And Transport Response Budgets Are Separate

The Trino application boundary SHALL account for `database_result_bytes` while
reading and converting database results and SHALL account for
`transport_response_bytes` after final MCP JSON serialization and before the
serialized response is written to its transport.

#### Scenario: Database result exceeds its budget

- **GIVEN** cursor consumption would exceed `database_result_bytes`
- **WHEN** the client reads the result
- **THEN** it stops consuming, closes database resources, and returns a bounded
  error without constructing the complete result

#### Scenario: Serialized MCP response exceeds its budget

- **GIVEN** the final envelope, escaping, keys, dictionaries, nested metadata,
  and result together exceed `transport_response_bytes`
- **WHEN** the transport response is prepared
- **THEN** the normal response is not written
- **AND** a reserved fixed error response is returned
- **AND** the error response itself fits within the configured transport budget

### Requirement: Invocation Work Has Cumulative Limits

Each Trino profiling invocation SHALL enforce cumulative limits for profiled
columns, statements, and elapsed time across nested operations. It MAY enforce
cumulative estimated scan bytes when the estimate is bounded and trustworthy.
The default starting limits SHALL be 100 columns, 150 statements, and 120
seconds unless benchmark evidence justifies documented alternatives.

#### Scenario: Wide-table profiling exhausts cumulative work

- **GIVEN** every individual SQL query remains within its per-query limits
- **WHEN** cumulative profiled columns, statements, scan estimate, or the
  invocation deadline is exhausted
- **THEN** the invocation fails closed before starting another operation
- **AND** no helper can reset the consumed budget

### Requirement: MCP Documentation Distinguishes Default And Opt-In Surfaces

Documentation SHALL state that default generator and default aggregate-only
Trino profiling tools return summaries, paths, counts, validation status, and
manifest context rather than source rows. Documentation SHALL separately
describe explicit opt-in row-returning capabilities, including that
`run_safe_select` is outside the source-literal-free guarantee.

#### Scenario: MCP documentation is checked

- **GIVEN** a document describes MCP responses or Trino tools
- **WHEN** the documentation contract test scans it
- **THEN** it does not make a server-wide source-free/privacy-safe claim that
  includes `run_safe_select`
- **AND** it uses the default aggregate-only versus explicit opt-in terminology
