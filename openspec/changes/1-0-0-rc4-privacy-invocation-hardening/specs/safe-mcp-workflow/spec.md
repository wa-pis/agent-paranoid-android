# Safe MCP Workflow Delta

## Requirements

### Requirement: Default Trino MCP Responses Are Source-Literal-Free

The default Trino MCP surface SHALL expose only metadata and bounded aggregate
profiling responses that do not return literal values copied from source cells.

#### Scenario: A profile contains distinct values in every source column

- **GIVEN** a source fixture whose every column contains a distinct literal,
  including non-PII-looking identifiers, statuses, dates, and free text
- **WHEN** a default Trino MCP profiling tool is invoked
- **THEN** no source literal is present in the response, error, or audit payload

### Requirement: Row-Returning Diagnostics Are Explicit Opt-In

Any retained row-returning Trino diagnostic SHALL be separately named,
disabled by default, explicitly operator-enabled, reviewed, and covered by the
documented audit and safety policy. It SHALL NOT be described as anonymous,
PII-free, or privacy-safe solely because heuristic masking was applied.

#### Scenario: The default tool surface is registered

- **GIVEN** no explicit row-diagnostic configuration is present
- **WHEN** the Trino MCP server registers its tools
- **THEN** no row-returning diagnostic is registered

### Requirement: Trino Work Is Bounded Per Invocation

Each Trino MCP invocation SHALL use one shared typed work budget across nested
profiling and query operations. The budget SHALL bound request size,
SQL/formula size, AST complexity and depth, projected columns, statements, and
response bytes, and SHALL fail closed before the corresponding limit is
consumed.

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
