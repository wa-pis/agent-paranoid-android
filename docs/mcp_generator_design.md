# Generator MCP Design Rationale

This document explains what the AI integration does, why its boundaries exist,
and where each responsibility lives in the codebase.

## Objective

An AI client should be able to inspect a source safely, create a reviewable
generation contract, generate deterministic synthetic data, validate it, and
export it without receiving production rows or gaining unrestricted filesystem
or database access.

The implementation keeps planning and orchestration in the AI layer while all
generation and validation decisions remain deterministic Python code.

The generic Trino `run_safe_select` tool is intentionally narrower than an
arbitrary read-only SQL client. It requires a literal bounded `LIMIT`, rejects
unrestricted projections and likely sensitive fields, and also rejects joins,
CTEs, subqueries, ordering, table functions, and `UNNEST`. Dedicated aggregate
profiling tools should be used for expensive multi-table analysis.

## Why Two MCP Servers

The integration deliberately separates source inspection from generation:

- `mcp_trino_server.py` has read-only access to an allowlisted Trino surface.
- `mcp_generator_server.py` has access only to a configured local workspace.

This separation follows least privilege. Database credentials do not need to be
available to the generator, and the Trino server does not need permission to
write output files. A compromised or mistaken tool call therefore has a smaller
blast radius.

```text
Trino or CSV
    |
    v
Safe profile metadata
    |
    v
DatasetSpec 1.0
    |
    v
Deterministic generator
    |
    v
Schema + relationship + constraint validation
    |
    v
Synthetic files + effective spec + report + manifest
```

Only safe profile metadata crosses the source/generator boundary: names, types,
null ratios, cardinalities, ranges, non-sensitive categories, and masked
patterns. Source rows and raw sensitive values do not cross it.

## Tool Logic

| Tool | Why it exists | Input | Written output | MCP response |
| --- | --- | --- | --- | --- |
| `profile_csv` | Convert a potentially sensitive CSV into reusable safe metadata | Workspace CSV path | Profile JSON | Counts and paths only |
| `infer_dataset_spec` | Turn safe observations into an explicit generation contract | Profile path or inline profile payload | DatasetSpec JSON/YAML | Contract summary |
| `plan_trino_dataset` | Build a review-first agent workspace from safe Trino metadata | `profile_table_safe` payload and generation settings | Profile, DatasetSpec, and plan | Plan summary and review paths |
| `approve_dataset_plan` | Continue only after the written DatasetSpec is reviewed | Planned workspace | Synthetic bundle | Row counts, validation, and manifest paths |
| `generate_dataset` | Run deterministic generation and validation | DatasetSpec, seed, count, optional format and structured rules | Synthetic bundle | Row counts and compact validation summaries |
| `validate_dataset` | Recheck a generated bundle without exposing its rows | Matching spec and generated folder | Optional report JSON | Validation report |
| `export_dataset` | Produce another supported format safely | DatasetSpec, seed, count, required format and optional structured rules | Fresh synthetic bundle | Row counts and compact validation summaries |

`export_dataset` intentionally regenerates data from a `DatasetSpec`. It does
not accept arbitrary row files, because a generic conversion tool could be used
to export production data.

## Data Flow

### Trino Source

1. The AI calls allowlisted metadata and aggregate profiling tools in
   `mcp_trino_server.py`.
2. The Trino server returns a compact safe profile payload.
3. The AI passes that payload directly to `infer_dataset_spec` as
   `profile_payload`.
4. The generator server validates the profile and writes a versioned spec.
5. The AI reviews or edits the spec, then requests generation.

No local copy of the source table is required.

### CSV Source

1. The CSV must be inside `TEST_DATA_AGENT_WORKSPACE_ROOT`.
2. `profile_csv` infers schema and safe distributions.
3. Sensitive columns retain masked patterns, never raw top values.
4. `infer_dataset_spec` creates the generation contract.
5. Generation uses distributions and a seed, not source-row shuffling.

Direct CSV and example-folder workflows compare complete generated rows against
the source before writing output. An exact match stops generation without
including the matched values in the error.

## Safety Decisions

### Workspace Boundary

Every generator MCP path is resolved against
`TEST_DATA_AGENT_WORKSPACE_ROOT`. Paths outside that root are rejected after
resolution, which also blocks traversal through existing symlinks.

MCP output files must be new, and generation folders must be new or empty. This
prevents accidental overwrites and avoids mixing a new synthetic dataset with
stale files from an earlier run.

Implementation: `src/test_data_agent/mcp_generator_server.py`.

### Shared Deployment Audit

Both MCP servers can write metadata-only, HMAC-authenticated audit events when
the operator configures an audit path and key. Audit records never contain tool
arguments, SQL, profiles, rows, return values, or exception messages. Invalid
audit configuration prevents tool execution. See
[MCP Audit Logging](operations/audit-logging.md).

### Safe Profiles

Fields marked sensitive, or inferred as sensitive from their name or semantic
type, may use only masked-pattern or synthetic-identifier distributions. Raw
categorical distributions for such fields are rejected.

Implementation: `src/test_data_agent/safety.py` and
`src/test_data_agent/generation/planner.py`.

### Synthetic Sensitive Values

Sensitive values are generated independently from the source. Emails use the
reserved `example.test` domain, phones use a fictional 555 range, and SSN-like
values use an invalid `000` prefix.

Implementation: `src/test_data_agent/generation/entity_generator.py`.

### No Rows In MCP Responses

Generator tools write datasets to the workspace and return only paths, row
counts, versions, and validation results. This keeps large payloads out of the
model context and reduces the chance of accidental disclosure in prompts,
logs, or chat history.

Business-rule generation follows the same boundary. The response contains a
rule fingerprint, rule/pass fail counts, validity, truncation status, and the
path to `business_validation_report.json`. Row-level errors remain in the
bounded workspace artifact.

### Structured Business Rules

`generate_dataset` and `export_dataset` accept at most one workspace
`business_rules_path` or inline `business_rules_payload`. Rule models forbid
unknown fields, cap list and expression sizes, and permit only constants,
field names, basic arithmetic, and explicit `sum`/`count` aggregate helpers.
The server also rejects requests whose DatasetSpec row counts and rule set
would exceed the configured estimated evaluation budget.

Before generation, `rules/contract.py` verifies every entity and field
reference against the DatasetSpec. It rejects values assigned to sensitive
fields and raw-looking emails, phones, SSNs, payment data, credentials, or
tokens in otherwise neutral rule literals. No output folder is published when
this boundary fails.

### Provenance Manifest

Every generated bundle includes `generation_manifest.json` with:

- package version
- DatasetSpec schema version
- SHA-256 fingerprint of the effective spec
- seed and output format
- row counts
- validation status
- optional business-rule fingerprint, rule count, pass/fail counts, validity,
  and error-truncation status
- `synthetic: true`
- `source_rows_copied: false`

The MCP validation tool requires this manifest and checks that its fingerprint
matches the supplied effective spec. This prevents validating a bundle against
an unrelated contract.

Implementation: `src/test_data_agent/io/artifacts.py`.

## Why DatasetSpec Is Versioned

`DatasetSpec` is the contract between the AI planner and deterministic code.
The serialized `schema_version: "1.0"` lets future versions evolve without
silently changing old contracts.

Version 1.0 validates:

- unique entity and field names
- valid primary-key references
- relationship entity/field references
- constraint entity/field references
- scoped privacy-rule references

Older specs without `schema_version` load as version 1.0 for compatibility.
Package version and spec schema version are independent.

Implementation: `src/test_data_agent/core/dataset.py` and
`src/test_data_agent/core/entity.py`.

## Why The Effective Spec Is Saved

Generation may override the seed, count, or output format supplied in the
original spec. The output folder therefore receives an effective
`dataset_spec.yaml` containing the values actually used. Validation and the
manifest fingerprint refer to this effective spec, making a run reproducible.

Implementation: `src/test_data_agent/io/workflows.py`.

## Output Location

For an output folder such as `generated/orders_run`, the bundle is:

```text
generated/orders_run/
  dataset_spec.yaml
  generation_manifest.json
  validation_report.json
  orders.csv
  customers.csv
```

There is one data file per entity. The extension is selected by the requested
CSV, JSON, or Parquet format.

## Module Ownership

- `core/`: versioned Pydantic domain contracts.
- `adapters/`: conversion of safe CSV, Trino, JSON, and older profile metadata.
- `profiling/`: schema, distribution, relationship, and constraint inference.
- `generation/`: seeded row generation and deterministic constraint solving.
- `validation/`: executable schema, relationship, and constraint checks.
- `io/`: artifact reading, writing, manifests, and reusable workflows.
- `safety.py`: profile and source-row reuse invariants.
- `mcp_trino_server.py`: read-only source-side tools.
- `mcp_generator_server.py`: workspace-side AI tools.
- `scripts/run_ai_demo.py`: local profile-to-CSV demonstration.

## Alternatives Intentionally Rejected

- One MCP server with both database credentials and broad filesystem access.
- Arbitrary unrestricted SQL tools.
- Returning raw or generated datasets directly in MCP responses.
- Giving the planning client `run_safe_select`; raw-SQL access is opt-in and
  not needed by `profile_table_safe` -> `plan_trino_dataset`.
- Exporting or converting arbitrary row files.
- Building output by copying, shuffling, or duplicating source rows.
- Treating free-form LLM reasoning as validation.

These alternatives are convenient, but they weaken isolation, auditability, or
the guarantee that output is synthetic.

## Verification

The main coverage is in:

- `tests/test_mcp_generator_server.py`
- `tests/test_safety.py`
- `tests/test_ai_trino_workflow.py`
- `tests/test_dataset_spec_contract.py`
- `tests/test_domain_agnostic_pipeline.py`

The local end-to-end demo is:

```bash
python3 scripts/run_ai_demo.py \
  --profile examples/trino_safe_profile.json \
  --output out/ai_demo \
  --count 100 \
  --seed 12345
```
