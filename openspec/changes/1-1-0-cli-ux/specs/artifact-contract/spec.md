# Artifact Contract Specification Delta

## Added Requirements

### Requirement: Single-Entity Output Matches Its Declared Format

Single-entity generation SHALL reject an output suffix that conflicts with the
selected serializer before generation or publication.

#### Scenario: Format and suffix agree

- **GIVEN** CSV, JSON, SQL, or Parquet output and its matching suffix
- **WHEN** generation succeeds
- **THEN** the primary file uses the requested serializer
- **AND** the manifest hashes that exact file

#### Scenario: Format and suffix conflict

- **GIVEN** a requested serializer and another format's suffix
- **WHEN** the command validates output
- **THEN** it fails with an actionable code `2` error
- **AND** no primary file, sidecar, staging directory, or success metadata is
  published

### Requirement: Single-Entity Overwrite Preserves Bundle Ownership

Overwrite SHALL replace either one existing primary target with no siblings,
or a validated complete bundle owned by the same primary data file. The
single-file case preserves the existing CLI contract; once sidecars exist,
manifest ownership is mandatory.

#### Scenario: The same bundle is regenerated

- **GIVEN** a complete valid manifest-owned single-entity bundle
- **WHEN** the same primary output is regenerated with `--overwrite`
- **THEN** the primary file and its sidecars are atomically replaced
- **AND** rollback restores the original complete bundle on failure

#### Scenario: Another primary or unrelated artifact exists

- **GIVEN** a different data file, stale file, unrelated sidecar, missing
  manifest, or invalid bundle in the destination
- **WHEN** overwrite is requested
- **THEN** publication fails before replacing any file
- **AND** the existing destination remains unchanged
- **AND** the error recommends a new output directory

#### Scenario: One legacy standalone target exists

- **GIVEN** only the requested primary output exists and there are no siblings
- **WHEN** the user repeats the command with `--overwrite`
- **THEN** the target is replaced and a complete bundle is published
- **AND** a future replacement is governed by its manifest
