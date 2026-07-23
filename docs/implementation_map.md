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
  Top-level `DatasetProfile` and versioned `DatasetSpec` contract validation.

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
- `agent-plan`
- `agent-approve`

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

## Generator MCP

`src/test_data_agent/mcp_generator_server.py`

Workspace-bounded tools profile CSV metadata, infer a DatasetSpec from a safe
file or inline MCP payload, generate/export fresh synthetic datasets, and
validate generated bundles. Generation and export accept strict, bounded
business-rule files or inline payloads. Tool responses contain summaries and
artifact paths, not rows. `src/test_data_agent/safety.py` and
`src/test_data_agent/rules/contract.py` reject unsafe sensitive distributions,
rule literals, workspace path escapes, and exact source CSV row reuse.

Generation bundles include `generation_manifest.json` for reproducibility and
provenance auditing. Rule-driven bundles also include a rule fingerprint and
compact business-validation summary.

## Agent Orchestration

`src/test_data_agent/agent.py`

The agent layer is a review-first state machine over existing deterministic
workflow helpers. `agent-plan` writes safe profile metadata, a reviewable
`DatasetSpec`, and an agent plan. It intentionally stops before generation.
`agent-approve` reloads the reviewed spec, generates synthetic data, validates
it, runs source-row reuse checks for CSV sources, and writes the generated
bundle.

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

`tests/test_mcp_generator_server.py`, `tests/test_safety.py`, and
`tests/test_ai_trino_workflow.py` cover MCP path isolation, inline Trino profile
handoff, raw-profile rejection, non-copy checks, manifests, and the complete
profile-to-CSV workflow.

`tests/test_agent.py` covers the review-first agent workflow and confirms that
planning does not write generated data.
