# Implementation Map

This is a map of the codebase for the domain-agnostic generator.

## Core Models

`src/test_data_agent/core/`

- `field.py`
  Field types and field profile/spec metadata.

- `entity.py`
  Entity/table profile and generation spec.

- `relationship.py`
  Relationship metadata with `confidence` and `status`.

- `constraint.py`
  Formula, temporal, conditional, and aggregate constraint metadata.

- `dataset.py`
  Top-level `DatasetProfile` and `DatasetSpec`.

## Profiling

`src/test_data_agent/profiling/`

- `schema_profiler.py`
  Streams a folder of CSV files and infers entities, fields, primary-key
  candidates, null ratios, types, sensitivity, distributions, and
  identifier-like columns without keeping the full dataset in memory.

- `distribution_profiler.py`
  Adds safe distributions. Sensitive fields receive masked patterns instead of
  raw top values.

- `cache.py`
  Stores and loads safe profile JSON for large local CSV folders. The cache is
  metadata-only and keyed by file names, sizes, and modification times.

- `relationship_profiler.py`
  Infers parent/child relationships by checking whether child identifier values
  are contained in parent key candidates.

- `constraint_miner.py`
  Infers formula, temporal, conditional required, and aggregate mapping
  constraints.

## Generation

`src/test_data_agent/generation/`

- `planner.py`
  Converts a `DatasetProfile` into a reviewable `DatasetSpec`.

- `entity_generator.py`
  Generates synthetic rows per entity from distributions and seed.

- `constraint_solver.py`
  Reconciles rows after initial generation:
  foreign keys, formulas, temporal ordering, conditional required fields, and
  aggregate mappings.

## Validation

`src/test_data_agent/validation/`

- `schema_validator.py`
  Checks generated rows match entity fields and field types.

- `relationship_validator.py`
  Checks child foreign keys point at generated parent keys.

- `constraint_validator.py`
  Checks formulas, temporal ordering, conditional required rules, and aggregate
  mappings.

- `reconciliation.py`
  Combines validation sections into a single report.

## CLI

`src/test_data_agent/cli.py`

New domain-agnostic commands:

- `profile-example`
- `infer-spec`
- `generate` with a YAML or JSON `DatasetSpec`
- `validate` with a YAML or JSON `DatasetSpec` and output folder
- `generate-from-example`

Compatibility paths are still supported during migration:

- `profile-csv`
- `generate-from-csv`
- `generate` with legacy JSON `GenerationSpec`
- `validate` with legacy JSON rows

## Trino MCP

`src/test_data_agent/mcp_trino_server.py`

Safe Trino tools are read-only and return compact metadata. In addition to
table and column profiles, the server exposes aggregate-only consistency
profiling for foreign keys, temporal ordering, formulas, conditional rules, and
aggregate mappings. These tools return counts, residuals, `confidence`, and
`status`; they do not return source rows.

## Tests

`tests/test_domain_agnostic_pipeline.py` covers the main pipeline:

- schema profiling
- relationship inference
- formula inference
- temporal rule inference
- conditional rule inference
- aggregate mapping inference/validation
- deterministic generation
- no copied source rows
- generated dataset validation
- CLI profile/infer/generate/validate flow
- safe profile cache reuse
