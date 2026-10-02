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
  Generates synthetic rows per entity from distributions and seed, then runs
  post-solve privacy and type checks before returning a dataset.

- `semantic_provider.py`
  Isolates optional synchronous semantic providers behind a fixed deadline,
  verifies same-request replay, and restricts string output to the
  `synthetic_` namespace.

- `constraint_solver.py`
  Reconciles rows after initial generation:
  foreign keys, formulas, temporal ordering, conditional required fields, and
  aggregate mappings.

## Selective Transformation Preparation (Private)

`src/test_data_agent/core/transformation_policy.py` validates reviewable
per-field behavior decisions and field coverage. `transformation_mapping.py`,
`transformation_csv.py`, and `transformation_yaml.py` validate inline/CSV
mapping declarations and restricted policy serialization. These parsers do not
authorize source-value preservation or transform rows.
Derived-field coverage reuses `rules.expressions.expression_references` to
parse bounded row-local arithmetic and require exact declared dependencies;
it does not evaluate formulas or establish financial/null/result-type semantics.
`transformation_report.py` computes value-free action-origin counts and shares:
replacement, synthetic and original. The private executor records actual
executed branches, not value equality. Explicit type/format transformation is
replacement; generated values remain synthetic after formatting. Dropped cells
are excluded; empty output shares are null. Shares round independently to two
decimal places and may sum to 99.99 or 100.01. Private manifest v2 exposes
`provenance`, replacing v1 `retention`. Legacy internal equality aggregates remain
for compatibility; neither reporting path authorizes preservation or weakens
independent safety checks. The report module neither transforms nor publishes.

`src/test_data_agent/io/mapping_snapshot.py`, `mapping_loader.py`,
`behavior_policy_files.py`, and `transformation_source.py` read bounded local
mapping, policy, and CSV-source byte snapshots. The core
`transformation_snapshot.py` and `transformation_approval.py` bind those exact
bytes and reviewed material. `io/transformation_receipt.py` handles a private
local interactive confirmation receipt; a receipt alone is not execution
permission. There is no public CLI/MCP source-preserving execution path yet.
`io/transformation_decisions.py` implements the local `transform-review --decide`
wizard: explicit per-column sensitivity answers, optional `--edit-actions`
configuration of the existing action models, fixed-snapshot validation and
atomic policy save. It creates no approval receipt. Shared
`transformation_source.load_policy_references` handles restricted references
both before review and after action edits; newly referenced files are also
revalidated before saving.
The private `prepare_csv_review_request` entry derives profile evidence from
the same fixed CSV bytes included in its approval request; callers cannot
provide an alternate profile to that entry. Receipt issue/verification still
reprofiles those bytes. The public `transform-review` CLI uses this path only
to display value-free decisions; it neither mints a receipt nor writes output.

`io/transformation_execute.py` owns the closed CSV execution prototype:
exact-text and typed replacement, synthesis, dependency-ordered derivation,
receipt-gated preservation, explicit null provenance and final validation.
`io/transformation_publish.py` publishes its CSV and mixed-origin manifest only
inside automatically deleted private test storage. Neither is public activation.

The format-independent RC target is input adapter -> common transformation and
validation -> output adapter. Current executor still combines CSV decoding,
execution and rendering; extraction is pending, not a completed architecture.
`io/transformation_input.py` now dispatches fixed-byte decoding for CSV and an
initial native nullable string/signed-integer/float64/boolean/decimal128 Parquet slice. Review, receipt revalidation,
execution/trace and final source comparison use that decoder. Unsupported native
Parquet types fail closed until typed input integration; no intermediate
CSV file replaces the source snapshot. Existing private CSV-named entry points
are retained during this extraction, not newly public interfaces.
First additional route is CSV -> SQL-script using a validated logical result,
not reparsing rendered CSV (which loses null and logical-type provenance).
Reuse `postgres_sql_export.quote_postgres_identifier` and `postgres_literal`
for PostgreSQL encoding. Do not route mixed-origin output through
`render_postgres_sql` by weakening its synthetic-generation checks.
`io/transformation_output.py` shares normalized scalar/privacy/whole-row checks
between private SQL and Parquet adapters. `io/transformation_parquet.py` builds
an explicit Arrow schema and bounds output bytes while writing. It does not
fabricate generation distributions to use `io/writers.typed_parquet_table`,
which remains the unchanged source-free generation writer. Final transformed
types are declared, not inferred from source after text replacement.
Output selection/schema/dialect must be
snapshot-bound before execution. Source-free generation/export stays separate.

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
- `transform-review` (read-only)
- `generate-from-csv`

## Database Configuration

`src/test_data_agent/postgres_config.py` and
`src/test_data_agent/trino_config.py` own environment parsing, credential-free
JDBC-style URL normalization, deterministic component-conflict checks,
typed exact/table-wildcard column selectors, allowlists, and resource budgets.
They discard the input URL before returning
the existing typed Python client configuration. `postgres_client.py` and
`trino_client.py` remain unaware of JDBC syntax; Trino receives only validated
allowlisted catalog/schema defaults.

The gated authentication candidate composes six driver methods through
`trino_auth.py` and `trino_client.py`, resolving runtime secret references without
saving credential values in profiles. The client reuses its auth object; the
OAuth HTTP adapter constrains direct token polling to the configured verified
HTTPS origin and remaining budgets. The explicit browser callback belongs only
to `io/commands.py`; its CLI registration remains in an unapplied candidate patch,
never an MCP callback or source-preservation receipt issuer.

`postgres_profiler.py` and `trino_profiling.py` expand qualified column
wildcards through bounded table metadata into immutable deterministic explicit
snapshots. Query builders receive only validated concrete identifiers; local
value policy remains a separate exact-field boundary.

`sql_query_source.py` owns the typed local query request, bounded stable file
read, strict PostgreSQL/Trino AST subset, physical table/column authorization,
explicit wildcard expansion, and source-free fingerprint. The paired
`sql_query_profiling.py` and `sql_query_adapters.py` modules perform no-row
derived schema inspection and aggregate-only virtual profile composition
through the existing clients and budgets. They expose no query-row result.

## Trino MCP

`src/test_data_agent/mcp_trino_transport.py`

Owns optional FastMCP loading, server construction, ordered tool registration,
and audit wrapping. It receives an allowlisted collection of application
services and does not own SQL validation or database policy.

`src/test_data_agent/mcp_trino_server.py`

Safe Trino tools are read-only and return compact metadata. In addition to
table and column profiles, the server exposes aggregate-only consistency
profiling for foreign keys, temporal ordering, formulas, conditional rules, and
aggregate mappings. These tools return counts, residuals, `confidence`, and
`status`; they do not return source rows.

## Generator MCP

`src/test_data_agent/mcp_generator_transport.py`

Owns optional FastMCP loading, server construction, ordered tool registration,
and audit wrapping. It receives workspace-bounded application services and
does not own path, payload, profile, or generation safety policy.

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

`src/test_data_agent/providers/openai.py`

Maps the safe exchange to the optional OpenAI Responses API adapter.

`src/test_data_agent/providers/gigachat.py`

Maps the same safe exchange to one bounded non-streaming strict-schema request
through the official `gigachat` SDK. It owns GigaChat authentication, fixed
verified-TLS endpoints, request/response budgets, redacted failures, and local
field-label restoration. It has no source, workspace, generation, approval,
database, SQL, or MCP authority.

`examples/reference_agent.py`

The runnable application-layer example composes planning, the exchange
adapter, status inspection, exact-fingerprint approval, deterministic
generation, and validation. Its baseline stand-in performs no network call,
and the command never auto-approves or returns rows. With the optional
`openai` extra, `test_data_agent.providers.openai.OpenAIAdvisorClient` maps
the same exchange to the OpenAI Responses API with bounded non-streaming
structured output and response storage disabled.
The review-first CLI may instead select the experimental `gigachat` extra;
the reference-agent script itself retains its existing deterministic/OpenAI
choices.

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

`tests/test_mcp_generator_transport.py` and
`tests/test_mcp_trino_transport.py` cover ordered audited transport
registration. `tests/test_mcp_generator_server.py`,
`tests/test_mcp_trino_server.py`, `tests/test_safety.py`, and
`tests/test_ai_trino_workflow.py` call application services directly to cover
path isolation, SQL allowlists, inline Trino profile handoff, raw-profile
rejection, non-copy checks, manifests, and the complete profile-to-CSV
workflow.

`tests/test_agent.py` covers the review-first agent workflow and confirms that
planning does not write generated data.
