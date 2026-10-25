# Implementation Map

This is a map of the codebase for the domain-agnostic generator.

Stable `1.6.0` retained the accepted `1.6.0rc5` runtime. Its finite fictional
transformation/session campaign and public verification subsequently completed;
see [stable evidence and coverage limits](release-evidence-1.6.0.md).
Existing “1.6 RC” sections identify that historical composition. Later feedback
additions follow the current contracts and module descriptions below. Release
acceptance grants no dataset permission or local preservation approval.

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
  metadata-only and keyed by file names, sizes, modification times, sampling
  configuration and normalized field-scoped local-category policy. Cache reads
  recheck that policy; changing or removing permission cannot reuse a broader
  cached profile. Inventory is streamed and count-bounded before sorting, with
  the caller's local/MCP deadline retained through fingerprinting.

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

## Selective Transformation (1.6 RC)

Published `1.6.0rc5` registers the local transformation commands, common-profile
workflow and configured SQL session consumers described below. Internal
`candidate` or `test` names do not determine public registration; the CLI and
running MCP composition do. Registration grants no dataset approval. The
[published evidence](release-evidence-1.6.0rc5.md) still leaves the broader
transformation/session acceptance campaign open.

`src/test_data_agent/core/transformation_policy.py` validates reviewable
per-field behavior decisions and field coverage. `transformation_mapping.py`,
`transformation_csv.py`, and `transformation_yaml.py` validate inline/CSV
mapping declarations and restricted policy serialization. These parsers do not
authorize source-value preservation or transform rows.
Derived-field coverage reuses `rules.expressions.expression_references` to
parse bounded row-local arithmetic and require exact declared dependencies;
it does not evaluate formulas or establish financial/null/result-type semantics.
`transformation_report.py` computes value-free action-origin counts and shares:
replacement, synthetic and original. The executor records actual
executed branches, not value equality. Explicit type/format transformation is
replacement; generated values remain synthetic after formatting. Dropped cells
are excluded; empty output shares are null. Shares round independently to two
decimal places and may sum to 99.99 or 100.01. Transformation manifest v2 exposes
`provenance`, replacing v1 `retention`. Legacy internal equality aggregates remain
for compatibility; neither reporting path authorizes preservation or weakens
independent safety checks. The report module neither transforms nor publishes.

`src/test_data_agent/io/mapping_snapshot.py`, `mapping_loader.py`,
`behavior_policy_files.py`, and `transformation_source.py` read bounded local
mapping, policy, and CSV-source byte snapshots. The core
`transformation_snapshot.py` and `transformation_approval.py` bind those exact
bytes and reviewed material. `io/transformation_receipt.py` handles a bound
local interactive confirmation receipt; a receipt alone is not execution
permission. Registered `transform-approve` issues a local interactive receipt;
`transform-execute` and workspace `execute_transformation` consume it through
the reviewed single-input application boundary. MCP cannot issue preservation
receipts.
Registration alone is neither dataset approval nor acceptance evidence.
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
to display value-free decisions; its decision editor can save the existing
policy, but neither mints a receipt nor writes transformed output.

The registered common-profile workflow lives in `io/transformation_batch_profile.py`,
`transformation_batch.py`, and `transformation_batch_receipt.py`: restricted
reference capture, exact ordered snapshot identity, shared review and local-TTY
receipt, linked final validation, and owned temporary mixed-origin publication.
The CLI exposes `transform-batch`; running generator MCP exposes
`common_transformation`. `temporary_batch_profile` materializes explicit
references into an owned temporary root without changing user files.
`temporary_batch_decisions` reuses the per-input editor there, requires explicit
field decisions and a final common SAVE, then revalidates the displayed snapshot.
SAVE creates no approval receipt. Explicit `create_csv_policies` plus a required
seed can initialize CSV policies from fixed schema evidence with unknown
sensitivity/drop-only proposals; the wizard requires action decisions for this
route. Native/captured sources still start from valid per-input proposals.
`save_batch_profile` publishes only behavior policies, validation-spec
and a common reference profile into a new/empty sibling directory below the
original reference root. It does not copy source snapshots or issue approval.
Source/reference bytes are rechecked and the published profile reloaded; changed
paths produce a new identity and require review. Publication failures leave no
trusted approval; a post-publication revalidation failure may leave configuration
requiring another review. Isolated CLI and installed SDK1/SDK2 stdio checks
cover this composition; they do not establish complete supervised acceptance
of the broader transformation/session campaign or approve any dataset.
Shared profile limits accept only total-input and output bytes; other
dimensions remain per-input policy settings.

`io/transformation_batch_workflow.py` owns typed review/validate/execute
orchestration and shared metadata serialization. The registered CLI dispatches
through `_candidate_common_main` and `_candidate_batch_main` in
`cli_transformation_candidate.py`; `mcp_transformation_candidate.py` supplies the
registered common-profile consumer. `_create_test_batch_mcp` isolates that same
consumer for tests; these internal helper names are not public Python APIs.
Execution/validation require the exact reviewed digest; receipt references stay
below the trusted root. MCP captures that root server-side and cannot issue
preservation receipts. Its strict argument-name check runs at the existing redacted transport
boundary before SDK parsing. By default consumers return value-free metadata
after temporary bundle cleanup. Execution can instead
retain a bundle in an explicitly named new direct-child destination below its
trusted root, using the same validation/receipt gates and atomic writer. Review
and validation cannot publish; traversal, nested or existing destinations fail.
No source rows enter returned metadata.
`transform-batch approve` delegates to `_candidate_batch_approve_main`, which
parses local common approval requests
and delegates to the same controlling-TTY issuer after checking the reviewed
digest and a new direct-child receipt path. Piped confirmation cannot approve;
MCP has no counterpart and neither parsing nor SAVE creates authority.

`io/transformation_execute.py` owns deterministic snapshot execution:
exact-text and typed replacement, synthesis, private dependency-ordered derivation,
receipt-gated preservation, explicit null provenance and final validation.
`io/transformation_publish.py` owns bounded atomic mixed-origin publication and
temporary acceptance storage. Registered CLI and workspace execution use the
shared application boundary; private derive is not enabled by those entrances.
Implementation registration alone is not dataset approval or campaign acceptance.

The format-independent RC target is input adapter -> common transformation and
validation -> output adapter. The shared executor still has CSV-named internal
entry points; they are implementation details, not permanent public API promises.
`io/transformation_input.py` dispatches fixed-byte decoding for CSV and the
native nullable string/signed-integer/float64/boolean/date32/decimal128 Parquet slice. Review, receipt revalidation,
execution/trace and final source comparison use that decoder. Unsupported native
Parquet types, including native timestamps and nested values, fail closed; no intermediate
CSV file replaces the source snapshot. Captured PostgreSQL/Trino envelopes use
the same bounded native decoder. `io/transformation_query_workflow.py` owns
configured capture for `transform-batch query-execute` and the running MCP
`configured_query_session` tool. Administrator configuration, read-only
allowlists and budgets authorize reads; later consumers reuse the frozen
capture without reconnecting. `io/transformation_query_sessions.py` owns MCP
session admission, expiry and shutdown cleanup. This is separate from ordinary
aggregate-only profiling and does not register a row-returning MCP tool.
SQL-script output uses a validated logical result,
not reparsing rendered CSV (which loses null and logical-type provenance).
Reuse `postgres_sql_export.quote_postgres_identifier` and `postgres_literal`
for PostgreSQL encoding. Do not route mixed-origin output through
`render_postgres_sql` by weakening its synthetic-generation checks.
`io/transformation_output.py` shares normalized scalar/privacy/whole-row checks
between transformation SQL and Parquet adapters. `io/transformation_parquet.py` builds
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

## Dataset artifacts

`src/test_data_agent/io/workflows.py` owns the common reviewed-spec bundle,
profile handoff, validation and staged publication. `io/writers.py` and
`io/readers.py` handle output representations and bounded reloading.
`io/csv_encoding.py` declares reversible manifest-bound CSV scalars;
`io/parquet_encoding.py` declares marked Parquet scalar encodings;
`io/sql_rows.py` decodes only generated INSERT data and never executes SQL.
`rules/typed_values.py` normalizes schema-aware validation operands in the core.
The [source/output matrix](reference/source-output-matrix.md) records coverage.

## CLI

`src/test_data_agent/cli.py`

Owns the public `main` entry point, parser composition, compatibility wrappers
and the common-profile dispatch. `cli_application.py` composes the other
command handlers; `cli_commands.py` owns dataset/utility dispatch,
`cli_agent.py` owns review-first agent dispatch and provider loading, and
`cli_doctor.py` owns doctor execution. Optional dependency discovery belongs to
`cli_dependencies.py`.

`src/test_data_agent/cli_parser.py`

Owns reusable argparse behavior, numeric argument validation, recovery hints,
structured parser-error rendering and the shared command registrars.
`cli.py:build_parser` separately registers `transform-batch`.

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
- `profile-parquet`, `profile-postgres`, `profile-query`
- `export-postgres-sql`
- `transform-review` (value-free review; optional local policy decision editor)
- `transform-approve` (local interactive receipt issuer)
- `transform-execute` (fixed-snapshot execution and publication)
- `transform-batch` (common create/review/approve/validate/execute and configured
  `query-execute`; only local controlling-TTY approval can issue a receipt)
- `generate-from-csv`

The complete 28-command inventory and compatibility aliases are recorded in
[Application Boundaries](reference/application-boundaries.md#cli-surface) and
`tests/fixtures/contracts/cli-parser-surface.json`.

## Database Configuration

`src/test_data_agent/postgres_config.py` and
`src/test_data_agent/trino_config.py` own environment parsing, credential-free
JDBC-style URL normalization, deterministic component-conflict checks,
typed exact/table-wildcard column selectors, allowlists, and resource budgets.
They discard the input URL before returning
the existing typed Python client configuration. `postgres_client.py` and
`trino_client.py` remain unaware of JDBC syntax; Trino receives only validated
allowlisted catalog/schema defaults.

Configured authentication composes six authenticated driver methods through
`trino_auth.py` and `trino_client.py`, resolving runtime secret references without
saving credential values in profiles. The client reuses its auth object; the
OAuth HTTP adapter constrains direct token polling to the configured verified
HTTPS origin and remaining budgets. The explicit browser callback belongs only
to `io/commands.py`; `cli_parser.py` registers it as
`profile-query --adapter trino --trino-oauth-browser`. It requires a local
interactive terminal and configured OAuth2 authentication. MCP never installs
that callback, and it cannot issue a source-preservation receipt.

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
artifact paths, not rows. Workspace resolution is enforced by the server;
`src/test_data_agent/safety.py` enforces safe distributions and source-row reuse
checks, while `src/test_data_agent/rules/contract.py` enforces rule references
and literal privacy.

`plan_dataset` gives AI clients one review-first entry point for a workspace
CSV file, CSV folder, or safe profile. It delegates to the same agent state
machine used by the CLI; `plan_trino_dataset` provides the parallel handoff for
safe inline Trino profiles.

The running `main` composition exposes 14 generator tools, including
`common_transformation` and `configured_query_session`, by injecting an owned
workspace and SQL session manager. The module-level SDK object exposes the 12
base tools and owns no configured SQL sessions. The full running inventory is
protected by `tests/fixtures/contracts/mcp-generator-tools.json`.

Generation bundles include `generation_manifest.json` for reproducibility and
provenance auditing. Rule-driven bundles also include a rule fingerprint and
compact business-validation summary.

## Agent Orchestration

`src/test_data_agent/agent.py`

Retains public compatibility functions, deterministic generation and completion
validation. Lifecycle ownership is split across `agent_planning.py`,
`agent_review.py`, `agent_approval.py`, `agent_recovery.py`, `agent_advising.py`
and `agent_status.py`; `agent_contracts.py` owns typed contracts and
`workspace_store.py` owns workspace publication.

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


## Explicit relational scenarios (Unreleased)

`core/relational_scenario.py` owns reviewed count declarations and count-only
observation types. `rules/relational_scenarios.py` prepares bounded plans bound
to effective spec/size/seed identity. `generation/relational_scenarios.py` owns
atomic generated-key allocation in native relationship dependency order;
`validation/relational_scenarios.py` independently reconciles final counts.
Generation and writer entry points enforce the final contract even when optional
reports are disabled. See the [relational synthesis contract](concepts/relational-synthesis-contract.md#explicit-relational-scenarios-unreleased).
