# RC6 Safe MCP Workflow Delta

## ADDED Requirements

### Requirement: Generator MCP Has a Bounded Transport Boundary

The generator MCP SHALL enforce a raw UTF-8 frame limit before JSON-RPC
materialization, a fresh shared invocation budget for each request, and a
bounded final JSON-RPC response before writing to stdout. An oversized request
or response SHALL use a fixed bounded error and SHALL NOT be retained in full
for parsing or logging.

#### Scenario: Oversized generator request

- **GIVEN** a generator MCP client sends a newline-framed request above the
  configured raw payload limit
- **WHEN** the transport reads the frame
- **THEN** it discards the frame without JSON parsing or tool dispatch
- **AND** it returns only a bounded local error, if a valid request ID can be
  safely reflected

#### Scenario: Generator response exceeds its budget

- **GIVEN** a generator tool produces a serialized JSON-RPC response larger
  than the invocation transport budget
- **WHEN** the production writer serializes the complete envelope
- **THEN** it replaces the response with a fixed bounded error before writing
  to stdout
- **AND** the request budget is released exactly once

### Requirement: Sensitive Numeric Profiles Are Non-Reversible

The default aggregate-only Trino profiling tools SHALL NOT return exact
extrema, percentiles, or equivalent reversible numeric values for columns
classified as sensitive. The same rule SHALL hold after legacy profile
conversion and in any generator planning artifact derived from the profile.

#### Scenario: Singleton sensitive numeric column

- **GIVEN** a sensitive numeric column contains one distinct non-null source
  value
- **WHEN** `profile_table_safe` or `profile_column_safe` profiles it
- **THEN** the response contains only bounded non-reversible shape metadata
- **AND** the source value is absent from the response, profile, DatasetSpec,
  advisor request, logs, and generated artifacts

### Requirement: JSON Resource Limits Apply Before Full Materialization

JSON profile, spec, and inline MCP payload processing SHALL bound depth, node or
container count, scalar size, and aggregate work before accepting an
untrusted object for recursive model validation. Parser recursion and memory
failures SHALL become bounded local input errors.

#### Scenario: Deep or object-heavy JSON payload

- **GIVEN** a payload is within its byte limit but exceeds a structural JSON
  limit
- **WHEN** the adapter receives it
- **THEN** it rejects or streams it without materializing the full object
- **AND** no unbounded recursive validation or tool work begins

### Requirement: MCP Admission And Backend Errors Are Bounded

The MCP server SHALL apply a global bound to active requests and shared Trino
work, rather than only bounding each request independently. Request state and
capacity SHALL be released exactly once on success, error, cancellation,
disconnect, timeout, and server teardown. Trino driver failures and backend
enumeration failures SHALL cross the transport boundary only as fixed bounded
local errors without provider-controlled text.

#### Scenario: Active-request capacity is exhausted

- **GIVEN** the active-request or shared-work cap is full
- **WHEN** a new MCP request arrives
- **THEN** the request is rejected before opening another backend operation
- **AND** the response is a fixed bounded capacity error
- **AND** existing request capacity is eventually released on every terminal
  path

#### Scenario: Trino backend returns an error

- **GIVEN** a Trino driver or catalog/schema enumeration operation raises an
  error containing backend-controlled text
- **WHEN** the MCP server handles the failure
- **THEN** the client receives only a bounded local reason and correlation
  metadata
- **AND** the backend error text is absent from the response, logs, and
  retained exception chain

### Requirement: Audit Admission Preserves Terminal Events

Audit-log capacity SHALL reject a new invocation before execution unless one
maximum-size terminal record is reserved. Once admitted, the invocation's
bounded `succeeded` or `failed` record SHALL NOT be dropped at the configured
admission threshold.

#### Scenario: Only the started record fits

- **GIVEN** the remaining audit capacity can hold `started` but not a maximum
  terminal record
- **WHEN** a new MCP tool invocation is attempted
- **THEN** the invocation is rejected before the tool executes
- **AND** no unmatched `started` record is appended

### Requirement: Opt-In Row Returning Has A Separate Privacy Contract

The explicit opt-in `run_safe_select` capability SHALL NOT inherit the default
aggregate-only privacy claim. It SHALL either restrict output to an allowlist
of non-sensitive fields or synthesize/mask every returned string and SHALL
document and test this separate contract against names, addresses, and values
that evade heuristic classification.

#### Scenario: Opt-in query returns an unrecognized identity string

- **GIVEN** a permitted query returns a name or address-like value that the
  heuristic classifier does not recognize
- **WHEN** the opt-in result is prepared for the MCP client
- **THEN** the separate row-privacy policy prevents the raw value from being
  returned
- **AND** the default aggregate-only guarantee remains scoped to default tools

#### Scenario: Opt-in query returns a composite value

- **GIVEN** a permitted query returns bounded maps, arrays, or row-like values
  containing nested strings
- **WHEN** the opt-in result is prepared for the MCP client
- **THEN** every nested string is masked while safe non-string values and
  container structure remain available
- **AND** excessive depth or value count fails closed before the response

### Requirement: Catalog And Schema Enumeration Policy Is Explicit

Catalog and schema discovery SHALL apply the same allowlist and metadata
exposure policy as other Trino MCP operations. Backend enumeration SHALL NOT
implicitly disclose unfiltered catalog, schema, error, or connection metadata.

#### Scenario: Enumeration contains a disallowed backend entry

- **GIVEN** a backend returns catalogs or schemas outside the configured
  allowlist
- **WHEN** an MCP discovery operation responds
- **THEN** disallowed entries are filtered before the response
- **AND** the response does not reveal the hidden entry through counts, error
  text, or ordering-dependent diagnostics
