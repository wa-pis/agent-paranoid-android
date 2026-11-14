## ADDED Requirements

### Requirement: Local Parquet Profiling Through Generator MCP

Generator MCP SHALL expose `profile_parquet` for a regular `.parquet` file
inside the configured workspace. It SHALL accept `input_path`, a new workspace
`.json` `output_path` and an optional `table_name` (defaulting to the source
stem). It SHALL use the existing bounded Parquet profile semantics, publish
the safe JSON artifact atomically without overwrite and return only the
workspace-relative artifact path, operation, source type and entity summaries.

#### Scenario: A client profiles and plans from Parquet

- **GIVEN** optional Parquet support and a valid, bounded workspace file
- **WHEN** an MCP client discovers and calls `profile_parquet`
- **THEN** the profile describes schema and aggregate evidence only, without source
  rows, cell values, private distinctness digests or embedded file metadata
- **AND** the artifact keeps exact, lower-bound and unknown evidence distinct
- **AND** the client can use the artifact with `plan_dataset` as a saved profile
  when evidence is sufficient, without bypassing human specification review

#### Scenario: A request is unsafe or cannot complete

- **GIVEN** a path escape, unsupported file, existing destination, malformed
  Parquet, a schema name containing a recognizable sensitive value, or a
  profiling budget or deadline violation
- **WHEN** the client calls `profile_parquet`
- **THEN** the operation fails without publishing a partial profile or replacing
  any existing file
- **AND** diagnostics do not disclose source values, private paths or decoder errors

#### Scenario: Parquet support is absent

- **GIVEN** the generator MCP package without the optional Parquet dependency
- **WHEN** a client calls `profile_parquet` with otherwise valid paths
- **THEN** it receives a fixed instruction to install the `parquet` extra
- **AND** no profile is written and the other tools remain available
