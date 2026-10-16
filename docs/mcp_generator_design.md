# Generator MCP Design Rationale

This document explains what the AI integration does, why its boundaries exist,
and where each responsibility lives in the codebase. Use
[MCP Permissions](reference/mcp-permissions.md) for the complete current tool
inventory and required process, database and review rights.

## Objective

The default review-first AI workflow should inspect a source safely, create a
reviewable generation contract, generate deterministic synthetic data,
validate it, and export it without receiving production rows or gaining
unrestricted filesystem or database access.

The implementation keeps planning and orchestration in the AI layer while all
generation and validation decisions remain deterministic Python code.

The explicit opt-in row-returning tool `run_safe_select` is intentionally
narrower than an arbitrary read-only SQL client. It requires a literal bounded
`LIMIT`, rejects unrestricted projections and likely sensitive fields, and also
rejects joins, CTEs, subqueries, ordering, table functions, and `UNNEST`.
It masks every returned string, including heuristic false negatives. Other
non-string source values may remain, so default aggregate-only tools should be
used for profiling.

## Why Two MCP Servers

The integration deliberately separates source inspection from generation:

- `mcp_trino_server.py` has read-only access to an allowlisted Trino surface.
- the ordinary synthetic tools in `mcp_generator_server.py` use a configured
  local workspace and need no database connection.

This separation follows least privilege. Database credentials do not need to be
available to the generator, and the Trino server does not need permission to
write output files. A compromised or mistaken tool call therefore has a smaller
blast radius.

The separate configured SQL transformation session can capture an authorized
database into owned temporary snapshots. It requires additional adapter,
network, database and storage rights plus its own activation acceptance; it is
outside the aggregate-profile-to-synthetic pipeline below. A local process
inherits its OS user's rights; the workspace setting alone is not a sandbox.

```text
Trino or CSV
    |
    v
Safe profile metadata
    |
    v
DatasetSpec 1.1 (legacy 1.0 remains readable)
    |
    v
Human review + fresh consent for the exact current spec
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

The [generator rights table](reference/mcp-permissions.md#generator-tool-rights)
describes all 14 console-registered tools, their inputs, effects and approvals.
The console entrypoint owns the workspace and session lifetime; the module-level
SDK object has only the 12 base tools. Transformation activation/release
acceptance is separate from registration. The ordinary
`approve_dataset_plan` receipt is not a source-preservation receipt and cannot
authorize transformation preservation; MCP has no preservation approval issuer.

`export_dataset` intentionally regenerates data from a `DatasetSpec`. It does
not accept arbitrary row files, because a generic conversion tool could be used
to export production data.

## Data Flow

### Trino Source

1. The AI calls allowlisted metadata and aggregate profiling tools in
   `mcp_trino_server.py`.
2. The Trino server returns a compact safe profile payload.
3. The AI passes that payload to `plan_trino_dataset` as `profile_payload`,
   with an explicit workspace, count and seed.
4. The generator server validates the profile, writes a versioned spec and
   stops before generation.
5. The client inspects the plan, presents the full current `dataset_spec.yaml`
   for human review and obtains fresh, explicit consent for that exact file.
6. After rechecking the file and fingerprint, it calls `approve_dataset_plan`
   with `reviewed_spec_sha256` from `inspect_dataset_plan`.

No local copy of the source table is required.

### CSV Source

1. The CSV must be inside `TEST_DATA_AGENT_WORKSPACE_ROOT`.
2. `plan_dataset` detects a CSV file or folder and invokes safe profiling.
3. Sensitive columns retain masked patterns, never raw top values.
4. The agent writes a reviewable generation contract and stops for approval.
5. The client inspects the plan, presents the full current specification and
   obtains fresh, explicit human consent. It rechecks the file and fingerprint
   before calling `approve_dataset_plan` with that reviewed fingerprint.
6. Approved generation uses distributions and a seed, not source-row
   shuffling. Editing the file requires another review and new consent; a
   summary or fingerprint alone is not human specification acceptance.

The lower-level `profile_csv` and `infer_dataset_spec` tools remain available
when a client needs explicit control over intermediate artifacts. These are
lower-level operations, rather than the persisted review-first plan lifecycle.
See [MCP usage](how-to/mcp.md) for the consent and resume procedure.

Direct CSV and example-folder workflows compare complete generated rows against
the source before writing output. An exact match stops generation without
including the matched values in the error.

## Safety Decisions

### Workspace Boundary

Ordinary generator MCP tool paths are resolved against
`TEST_DATA_AGENT_WORKSPACE_ROOT`. Paths outside that root are rejected after
resolution, which also blocks traversal through existing symlinks.
Owned runtime temporary storage and separately configured audit/authentication
files have different locations; see [minimum process rights](reference/mcp-permissions.md#minimum-process-rights).

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
type, may use masked-pattern or synthetic-identifier distributions. Sensitive
integer/float fields also support coarse `numeric_shape` or a `numeric`
distribution with a non-identity scale factor. Raw categorical distributions
for sensitive fields are rejected; exact sensitive Trino extrema and percentiles
are not accepted as safe profiles.

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

Business-rule generation follows the same boundary. Direct `generate_dataset`
and `export_dataset` responses include the rule fingerprint, rule/pass fail
counts, validity, truncation status and `business_validation_report_path`.
`approve_dataset_plan` returns its compact generation summary and bundle paths;
the rule summary and report remain in the hashed workspace bundle rather than
separate response keys. Bounded, value-free rule diagnostics remain in that
artifact.

### Structured Business Rules

Business rules may be embedded in the reviewed `DatasetSpec`, so the same
rules reach deterministic generation, review-first approval, validation and
export regardless of the source or output adapter. `generate_dataset` and
`export_dataset` also accept one workspace `business_rules_path` or inline
`business_rules_payload` when the spec has no embedded rules. Combining rule
sources is rejected; supplied rules are saved in the effective spec.
Rule models forbid
unknown fields, cap list and expression sizes, and permit only constants,
field names, basic arithmetic, and explicit `sum`/`count` aggregate helpers.
The server also rejects requests whose DatasetSpec row counts and rule set
would exceed the configured estimated evaluation budget.

Before generation, `rules/contract.py` verifies every entity and field
reference against the DatasetSpec. Literal assignments and comparisons against
sensitive fields fail closed. Other literals undergo the shared content, size
and type checks, including exact DECIMAL shape validation and its explicitly
reviewed non-sensitive `numeric_measure` handling. No output folder is
published when this boundary fails.

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
matches the supplied effective spec. Manifest output hashes also bind the data,
validation artifacts and any `business_validation_report.json`; missing or
changed bound artifacts fail validation. This prevents validating a bundle
against an unrelated contract or accepting a deleted rule report.

Implementation: `src/test_data_agent/io/artifacts.py`.

Review-first agent generation also writes `approval_receipt.json` beside the
workspace plan. The receipt binds the random plan identifier and safe-profile
fingerprint to the exact effective-spec fingerprint confirmed by the caller.
The fingerprint is recomputed immediately before generation; mismatches fail
without publishing output.

## Why DatasetSpec Is Versioned

`DatasetSpec` is the contract between the AI planner and deterministic code.
Newly constructed specs use `schema_version: "1.1"`; readers explicitly support
both `1.0` and `1.1`. The serialized version permits evolution without silently
changing old contracts. Exact `decimal` fields require `1.1` and their declared
precision/scale and `decimal_range`; they cannot be silently read as floats.

Both supported versions validate:

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
CSV, JSON, SQL, or Parquet format. `plan_dataset` exposes CSV, JSON and Parquet
selection; `plan_trino_dataset` and direct generation/export also accept SQL.
See the
[source/output matrix](reference/source-output-matrix.md) for interface details.

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

These restrictions describe the ordinary aggregate-profile-to-synthetic
pipeline. Separately registered mixed-origin transformation consumers remain
behind their distinct snapshot, classification and local-receipt contracts;
this pipeline grants them no source-preservation authority.

- One MCP server with both database credentials and broad filesystem access.
- Arbitrary unrestricted SQL tools.
- Returning raw or generated datasets directly in MCP responses.
- Giving the planning client the explicit opt-in row-returning tool
  `run_safe_select`; it is not needed by `profile_table_safe` ->
  `plan_trino_dataset`.
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
