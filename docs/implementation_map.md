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

Owns the stable `main` entry point, application dispatch, provider loading,
and doctor execution.

`src/test_data_agent/cli_parser.py`

Owns reusable argparse behavior, numeric argument validation, recovery hints,
structured parser-error rendering, and registration of every public CLI
command.

`src/test_data_agent/cli_presenter.py`

Owns shared human and JSON error rendering, validation-result output and exit
codes, bounded review-first agent presentation, and utility command output.

`src/test_data_agent/cli_contract.py`

Owns versioned machine-readable CLI errors and the typed doctor result passed
between diagnostics and presentation.

Public dataset-oriented commands:

- `profile-example`
- `infer-spec`
- `generate` with a YAML or JSON `DatasetSpec`
- `validate` with a YAML or JSON `DatasetSpec` and output folder
- `generate-from-example`
- `agent-plan`
- `agent-review`
- `agent-advise`
- `agent-approve`

- `profile-csv`
- `generate-from-csv`

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

`plan_dataset` gives AI clients one review-first entry point for a workspace
CSV file, CSV folder, or safe profile. It delegates to the same agent state
machine used by the CLI; `plan_trino_dataset` provides the parallel handoff for
safe inline Trino profiles.

Generation bundles include `generation_manifest.json` for reproducibility and
provenance auditing. Rule-driven bundles also include a rule fingerprint and
compact business-validation summary.

## Agent Orchestration

`src/test_data_agent/agent.py`

The agent layer is a review-first state machine over existing deterministic
workflow helpers. `agent-plan` writes safe profile metadata, a reviewable
`DatasetSpec`, and an agent plan. It intentionally stops before generation.
`agent-status` computes the current effective-spec fingerprint.
`agent-review` builds a typed metadata-only checklist from the current spec,
including privacy flags and field generation metadata but no distribution
values or rows.
`agent-advise` lazily loads an optional provider adapter, validates its
structured proposal through the provider-neutral contract, updates the pending
spec, and requires another review.
`agent-approve` requires that exact reviewed fingerprint, verifies the stored
safe profile, generates synthetic data, validates it, runs source-row reuse
checks for CSV sources, and writes the generated bundle plus an approval
receipt. The generated bundle includes `agent_completion.json`.
`agent-recover` revalidates that checkpoint, profile/spec fingerprints,
manifest, rows, validation report, and source-row non-reuse before publishing
missing result metadata. It never calls generation.

`src/test_data_agent/advisor.py`

The provider-neutral model boundary fingerprints safe metadata and the
baseline `DatasetSpec`, validates structured proposals, preserves core-owned
safety settings, and performs no generation. `advise_agent_workspace` persists
the validated exchange as `advisor_review.json`, atomically updates the pending
spec, and leaves generation behind the existing fingerprint approval gate.
`build_agent_advisor_request` and `apply_agent_advisor_proposal` expose the
same boundary to external model clients through structured JSON without a
provider SDK. `AdvisorExchange` adds immutable trusted instructions and the
generated proposal schema while keeping the request explicitly untrusted.
`ExchangeDatasetAdvisor` adapts an application-owned structured-output client
to `DatasetAdvisor`, passes a defensive exchange copy, and validates the
untrusted response against the original fingerprint-bound request.

`examples/reference_agent.py`

The runnable application-layer example composes planning, the exchange
adapter, status inspection, exact-fingerprint approval, deterministic
generation, and validation. Its baseline stand-in performs no network call,
and the command never auto-approves or returns rows. With the optional
`openai` extra, `test_data_agent.providers.openai.OpenAIAdvisorClient` maps
the same exchange to the OpenAI Responses API with bounded non-streaming
structured output and response storage disabled.

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
