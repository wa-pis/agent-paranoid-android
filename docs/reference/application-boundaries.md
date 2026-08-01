# Application Boundary Baseline

This inventory freezes the observable surfaces and current dependency
direction before the 1.0 application-boundaries refactor moves code. It does
not declare internal modules public or approve a contract change.

The golden fixtures under `tests/fixtures/contracts/` remain authoritative.
This page makes their ownership and the current architectural pressure visible
in one place so each extraction can be reviewed against the same baseline.

## Process Entry Points

- `test-data-agent` -> `test_data_agent.cli:main`
- `test-data-agent-mcp-generator` ->
  `test_data_agent.mcp_generator_server:main`
- `test-data-agent-mcp-trino` ->
  `test_data_agent.mcp_trino_server:main`

These entry-point names and targets must continue to resolve throughout the
refactor. A thin compatibility wrapper may retain an old target while the
composition root moves internally.

## Public Python Imports

The exact 57-name `test_data_agent.__all__` baseline is protected by
`public-python-api.json`. The exports are grouped below only to show
ownership; grouping does not change their compatibility status.

Core data, result, error, and version contracts:

- `DATASET_SPEC_SCHEMA_VERSION`, `DatasetProfile`, `DatasetSpec`
- `DatasetGenerationResult`, `DatasetValidationReport`
- `CliErrorCode`, `CliErrorDetail`, `CliErrorResponse`
- `__version__`

Agent models and enums:

- `AgentApprovalReceipt`, `AgentCompletionCheckpoint`
- `AgentFieldReference`, `AgentFieldSummary`,
  `AgentGenerationSummary`
- `AgentNextAction`, `AgentPlanSummary`,
  `AgentRecoverySummary`
- `AgentRelationshipSummary`, `AgentRequest`, `AgentResult`
- `AgentReviewEntitySummary`, `AgentReviewFieldSummary`
- `AgentReviewReport`, `AgentReviewSafetySummary`,
  `AgentReviewState`
- `AgentSourceType`, `AgentWorkspaceStatus`

Advisor contracts:

- `AdvisorContractError`, `AdvisorExchange`,
  `AdvisorExchangeClient`
- `AdvisorProposal`, `AdvisorRequest`,
  `AdvisorReviewArtifact`
- `DatasetAdvisor`, `ExchangeDatasetAdvisor`

Public operations:

- `advise_agent_workspace`, `advise_dataset_spec`
- `advisor_proposal_json_schema`, `apply_agent_advisor_proposal`
- `approve_agent_workspace`, `build_agent_advisor_exchange`
- `build_agent_advisor_request`, `build_advisor_exchange`
- `build_advisor_request`, `build_advisor_review_artifact`
- `detect_agent_source_type`, `generate_dataset`
- `generate_dataset_bundle`, `infer_dataset_spec`
- `inspect_agent_workspace`, `plan_agent_profile`
- `plan_agent_request`, `recover_agent_workspace`
- `review_agent_workspace`, `solve_constraints`
- `validate_advisor_proposal`, `validate_dataset`

## CLI Surface

`cli-parser-surface.json` freezes these 19 commands:

- `generate`, `profile-example`, `infer-spec`, `profile-csv`
- `generate-from-csv`, `validate`, `generate-from-example`
- `demo`, `doctor`, `audit-verify`
- `agent-plan`, `agent-approve`, `agent-recover`
- `agent-advise`, `agent-advisor-request`
- `agent-advisor-apply`, `agent-status`, `agent-review`
- `examples`

Compatibility aliases remain:

- `generate-from-csv-folder` -> `generate-from-example`
- `profile-csv-folder` -> `profile-example`

The parser, option defaults, structured errors, human output, and exit-code
meanings remain owned by `cli_parser.py`, `cli_contract.py`, and
`cli_presenter.py`. Moving handlers out of `cli.py` must not change
those contracts.

## MCP Tool Surfaces

`mcp-generator-tools.json` freezes these generator tools:

- `approve_dataset_plan`, `export_dataset`, `generate_dataset`
- `infer_dataset_spec`, `inspect_dataset_plan`, `plan_dataset`
- `plan_trino_dataset`, `profile_csv`,
  `recover_dataset_plan`, `validate_dataset`

`mcp-trino-tools.json` freezes these Trino tools:

- `describe_table`, `list_catalogs`, `list_schemas`,
  `list_tables`
- `profile_aggregate_mapping`, `profile_column`
- `profile_conditional_allowed_values`,
  `profile_conditional_required`
- `profile_foreign_key`, `profile_formula_rule`
- `profile_table`, `profile_table_safe`
- `profile_temporal_ordering`, `sample_rows_masked`

Tool names, descriptions, input/output schemas, ordering, audit wrapping, and
safety behavior remain compatibility-gated. Transport extraction must not move
SQL, path, profile, or generation policy into FastMCP registration.

## Artifact Contracts

The versioned contract catalog contains:

- `advisor-exchange.json`, `artifact-layout.json`
- `cli-agent-plan.json`, `cli-parser-surface.json`
- `dataset-spec.json`, `generation-manifest.json`
- `mcp-generate.json`, `mcp-generator-tools.json`
- `mcp-plan.json`, `mcp-trino-tools.json`
- `public-python-api.json`, `validation-report.json`

The review-first agent workspace publishes these stable names:

- `agent_request.json`, `agent_plan.json`, `profile.json`
- `dataset_spec.yaml`, optional `advisor_review.json`
- `approval_receipt.json`, `agent_result.json`
- `generated/`, containing `agent_completion.json`

Generated bundles retain entity data files plus
`generation_manifest.json`, `validation_report.json`, and the
reviewed spec/profile artifacts. Rule-driven generation may add
`business_validation_report.json`. Additive files or fields still require
the existing contract review; rename or removal is breaking.

## Current Dependency Direction

The current dependencies after completed extraction increments are:

| Owner | Current dependencies |
| --- | --- |
| `__init__.py` | agent, advisor, core, CLI contracts, generation, I/O workflows, validation, version |
| `cli.py` | public entry point, parser/presenter contracts, and compatibility wrappers |
| `cli_application.py` | handler composition and first-owner command dispatch |
| `cli_agent.py` | `agent-*` request translation, handler dispatch, lifecycle services, provider adapter, and presenters |
| `cli_commands.py` | dataset and utility handlers, I/O workflows, audit, demo, rules, and presenters |
| `cli_dependencies.py` | optional-extra module catalog, injected availability inspection, and normalized installation errors |
| `cli_doctor.py` | installation diagnostics, synthetic quickstart smoke, and redacted optional-capability smoke orchestration |
| `agent.py` | compatibility exports plus deterministic generation and completion validation |
| `agent_contracts.py` | core field, relationship, and settings models only |
| `agent_planning.py` | adapters, contracts, core, generation planning, profiling, safety, and workspace-store port |
| `agent_review.py` | contracts, planning settings validation, bounded artifact readers, profile safety, and injected workspace status |
| `agent_approval.py` | contracts, review context, bounded artifact readers, workspace-store publication, and injected status/generation ports |
| `agent_recovery.py` | contracts, review/approval context, bounded artifact readers, workspace-store publication, and injected completion validation |
| `agent_advising.py` | advisor contracts, review context, bounded artifact readers, atomic spec publication, and injected workspace status |
| `agent_status.py` | contracts, bounded artifact readers, review/recovery inspection, and read-only lifecycle reconstruction |
| `workspace_store.py` | typed workspace paths and transitions, core profile/spec models, bounded artifact I/O |
| Generator MCP server | agent, adapters, audit, core, I/O, rules, safety, generator transport factory |
| Trino MCP server | audit, core privacy, SQL parsing, Trino client, Trino transport factory |
| MCP transport modules | optional FastMCP and audit wrapping around supplied callables |
| generation/profiling/validation/rules | core models and pure policy helpers |

The two server modules currently import their transport factory to assemble the
executable server. `agent.py` and `cli.py` remain compatibility owners around
their extracted services; `mcp_trino_server.py` retains responsibilities named
in the active OpenSpec. These boundaries are not permission to reverse safety
dependencies during extraction.

The target direction remains:

```text
CLI/MCP composition -> application services -> policy/core -> typed ports
                                              -> filesystem/database adapters
```

Safety policy must be callable below transports. Core and application services
must not import CLI presentation or FastMCP registration. Compatibility modules
may import extracted implementations temporarily, but extracted services must
not import those wrappers back.

### Workspace Store Migration

`workspace_store.py` now owns workspace artifact paths, typed persistence ports,
atomic plan publication, and completion-marker publication. `agent.py` remains
the compatibility owner for its existing constants, `AgentArtifacts`, and
`agent_artifacts` import paths while lifecycle services are extracted.

Planning writes into a sibling staging directory and renames the complete
workspace into place only after every artifact is ready. A failed plan restores
an existing empty workspace and removes staging data. Completion publishes the
approval receipt before the atomic `agent_result.json` state marker, preserving
the existing checkpoint-based recovery behavior.

### Planning Service Migration

`agent_contracts.py` now owns lifecycle models and `agent_planning.py` owns safe
profile-to-plan orchestration. Public package and `agent.py` imports remain
compatible, and `workspace_store.py` re-exports `AgentArtifacts`. Direct service
calls enforce source-path and profile-safety checks before publishing artifacts.

`agent_review.py` now owns metadata-only review report construction and review
fingerprint refresh. The compatibility wrapper injects `inspect_agent_workspace`;
the extracted service has no reverse dependency on `agent.py`, CLI, or MCP
transports and rejects a replaced spec symlink before reading it.

`agent_approval.py` now owns the reviewed-fingerprint gate, idempotent completed
result handling, and atomic receipt/result publication. Its typed ports inject
workspace inspection and deterministic generation without a reverse dependency
on `agent.py`, CLI, or MCP transports.

`agent_recovery.py` now owns recovery fingerprint checks, interrupted bundle
publication, and recovery-state inspection. Its typed validation port preserves
tamper detection without importing `agent.py`, CLI, or MCP transports.

`agent_advising.py` now owns safe advisor requests/exchanges, persisted proposal
resume, and fingerprint-bound spec application. It remains metadata-only and
injects workspace inspection without importing `agent.py`, CLI, or MCP
transports.

### CLI Doctor Service Migration

`cli_doctor.py` now owns installation diagnostics and capability smoke
orchestration. `cli.py` retains compatibility wrappers and injects its current
module importer and smoke callables, preserving existing output, redaction, and
test override points while command dispatch remains unchanged.

`cli_dependencies.py` centralizes optional-extra discovery and installation
errors for doctor capability checks and OpenAI advice. Importers and loaders
remain injectable so direct service calls preserve fail-closed behavior.

`cli_agent.py` now owns review-first `agent-*` request translation and command
handling. `cli.py` keeps the public entry point and compatibility helpers, then
injects those helpers into the extracted handler without changing parser or
presenter contracts.

`cli_commands.py` now owns dataset and utility command handling, including the
direct business-rule bridge. `cli.py` keeps the existing business-rule
compatibility helper while injecting doctor and rule dependencies.

`cli_application.py` now composes the utility, dataset, and agent handlers and
dispatches to the first handler that owns a command. `cli.py` retains the public
entry point and a thin `run_command` compatibility wrapper with its existing
test override points.

## Per-Increment Review

Each refactor pull request must:

1. name the responsibility being moved and the old compatibility owner;
2. preserve the golden fixtures listed above without regeneration;
3. add direct-service tests for the moved safety boundary;
4. add or tighten an architecture dependency rule when a new boundary exists;
5. run the focused tests plus the relevant public contract gates.

See [Public Stability](stability.md) for change classification and the active
[OpenSpec](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/application-boundaries-refactor/proposal.md)
for the staged extraction plan.
