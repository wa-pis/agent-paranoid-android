# Safe MCP Workflow Delta

## ADDED Requirements

### Requirement: Default Trino MCP Responses Are Source-Literal-Free

The default Trino MCP surface SHALL expose only metadata and bounded aggregate
profiling responses. Successful responses, typed errors, and metadata-only
audit records SHALL NOT contain literal values copied from source cells.

#### Scenario: A profile contains distinct values in every source column

- **GIVEN** a source fixture whose every column contains a distinct literal,
  including non-PII-looking identifiers, statuses, dates, and free text
- **WHEN** a default Trino MCP profiling tool is invoked
- **THEN** no source literal is present in the response, error, or audit payload

### Requirement: RC4 Has No Row-Sampling Diagnostic

The RC4 public MCP and Python compatibility surfaces SHALL NOT expose
`sample_rows_masked` or another masked-row sampling diagnostic. A future
row-returning diagnostic SHALL require a separate OpenSpec change with an
independent configuration flag, catalog/schema/table/column allowlists, no
wildcard projection, strict row and column limits, metadata-only audit
logging, and visible capability status.

#### Scenario: RC4 tool surfaces are registered

- **GIVEN** the RC4 Trino MCP server and its public compatibility module are
  loaded
- **WHEN** the Trino MCP server registers its tools
- **THEN** `sample_rows_masked` is not registered or exported as a supported
  RC4 tool
- **AND** `run_safe_select` is registered only when its independent explicit
  opt-in is enabled

### Requirement: Opt-In Safe Select Is Not Source-Free

The opt-in `run_safe_select` capability SHALL remain disabled by default and
separate from the aggregate-only toolset. Its bounded result MAY contain
allowed non-PII source values and SHALL NOT be described as source-free,
anonymous, PII-free, or privacy-safe solely because heuristic masking is
applied. Its errors and metadata-only audit records SHALL NOT contain returned
values or source literals.

#### Scenario: Safe select is explicitly enabled

- **GIVEN** `TRINO_ENABLE_SAFE_SELECT=true` and valid catalog/schema allowlists
- **WHEN** a bounded read-only query is executed
- **THEN** the query is handled under the independent safe-select policy
- **AND** the result is not covered by the default aggregate-only
  source-literal-free response guarantee
- **AND** audit records contain operation status and error type only

### Requirement: Default Toolset Is Tested As A Whole

The source-literal-free guarantee SHALL be tested against the actual default
tool list returned by the same composition root used in production, not only
against individual profiling functions.

#### Scenario: Every default Trino tool is exercised

- **GIVEN** a fixture with distinct source literals in every supported type
- **WHEN** each registered default Trino tool is invoked through its direct
  service and MCP transport boundaries
- **THEN** successful responses, validation/database errors, and nested JSON
  values contain none of the source-cell literals
- **AND** metadata-only audit records contain no arguments, results, or source
  literals

### Requirement: Trino Work Is Bounded Per Invocation

Each Trino MCP invocation SHALL use one shared typed work budget across nested
profiling and query operations. The budget SHALL bound request size,
SQL/formula size, AST complexity and depth, projected columns, statements, and
response bytes, and SHALL fail closed before the corresponding limit is
consumed. A raw transport payload limit SHALL be enforced before MCP argument
parsing, and a canonical argument limit SHALL be enforced after schema
validation.

The budget SHALL be fresh per invocation, isolated between concurrent
invocations, shared with nested helpers, monotonic, and non-resettable.
Response bytes SHALL be consumed incrementally before a complete oversized
response is materialized.

#### Scenario: Nested profiling exceeds the shared budget

- **GIVEN** table profiling starts with a bounded invocation budget
- **WHEN** nested column profiling exhausts any shared allowance
- **THEN** the invocation stops with a bounded typed error and performs no later
  query or column operation

#### Scenario: Preflight work exceeds its budget

- **GIVEN** request, SQL, or AST validation can determine that a limit is
  exceeded before database access
- **WHEN** the Trino MCP operation is submitted
- **THEN** it fails before opening a connection or cursor
