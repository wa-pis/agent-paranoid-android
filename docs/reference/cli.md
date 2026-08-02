# CLI Reference

The executable is `test-data-agent`.

Use built-in help as the authoritative option reference:

```bash
test-data-agent
test-data-agent --help
test-data-agent examples
test-data-agent COMMAND --help
test-data-agent --version
```

Running `test-data-agent` without a command is not an error. It prints the
available commands, the safest starting points, and copy-ready quickstart
commands.

## Commands

| Command | Purpose | Primary output |
| --- | --- | --- |
| `examples` | Show complete examples for common workflows | Terminal guide |
| `demo` | Run the installed package offline with a bundled fictional fixture | Synthetic CSV bundle |
| `doctor` | Check installation and run a temporary smoke generation | Terminal report |
| `audit-verify` | Verify an HMAC-authenticated MCP audit log | Verification summary |
| `profile-csv` | Profile one CSV into safe metadata | Profile JSON |
| `profile-example` | Profile a folder with one CSV per entity | Profile JSON |
| `infer-spec` | Infer a reviewable `DatasetSpec` | YAML or JSON spec |
| `generate-from-csv` | Run the complete single-table workflow | Data file and review artifacts |
| `generate-from-example` | Run the complete related-table workflow | Dataset bundle |
| `generate` | Generate from a spec or safe profile | Data file or dataset bundle |
| `validate` | Validate a generated dataset folder against a `DatasetSpec` | Validation report |
| `agent-plan` | Profile and prepare a spec, then stop for review | Review workspace |
| `agent-advise` | Ask an installed provider for validated spec changes | Pending workspace status |
| `agent-advisor-request` | Export safe metadata for an external AI advisor | Request or exchange JSON |
| `agent-advisor-apply` | Validate and apply an external proposal | Pending workspace status |
| `agent-status` | Inspect agent phase and next action without changing it | Terminal or JSON status |
| `agent-review` | Inspect the current spec as a metadata-only approval checklist | Terminal or JSON report |
| `agent-approve` | Generate from an approved agent workspace | Dataset bundle |
| `agent-recover` | Revalidate and finish an interrupted approval | Missing completion metadata |

Aliases:

- `profile-csv-folder` is an alias for `profile-example`;
- `generate-from-csv-folder` is an alias for `generate-from-example`.

## Choose A Workflow

For a first offline run after installation:

```bash
test-data-agent demo --output out/demo
```

The destination must not exist. The command uses a bundled fictional fixture,
seed `20260801`, and no network or optional integration. The output contains
synthetic CSV rows, a safe profile, the effective spec, a validation report,
and a generation manifest.

For one CSV file, use the complete workflow:

```bash
test-data-agent generate-from-csv data/customers.csv \
  --count 100 \
  --seed 12345 \
  --format csv \
  --output out/customers.csv
```

For a folder containing one related table per CSV file:

```bash
test-data-agent generate-from-example data/example_dataset \
  --count 100 \
  --seed 12345 \
  --format csv \
  --output out/generated
```

For a reviewed `DatasetSpec`, pass the spec as the positional input:

```bash
test-data-agent generate dataset_spec.yaml \
  --seed 12345 \
  --format csv \
  --output out/generated
```

For previously reviewed safe profile metadata, use `--profile`:

```bash
test-data-agent generate --profile profile.json \
  --count 100 \
  --seed 12345 \
  --format csv \
  --output out/customers.csv
```

`generate` accepts exactly one of a `DatasetSpec` path or `--profile`. Spec
generation writes a dataset folder. Single-table profile generation writes one
data file and requires `--count` and `--seed`.

## Common Generation Options

| Option | Meaning |
| --- | --- |
| `--count N` | Number of generated rows per entity or an override |
| `--seed N` | Non-negative deterministic seed |
| `--format csv|json|sql|parquet` | Output format |
| `--mode valid|mixed|negative|edge|load_test` | Generation mode |
| `--invalid-ratio R` | Invalid share from `0` to `1` for applicable modes |
| `--business-rules PATH` | Reviewed YAML or JSON rule file |
| `--output PATH` | Output file or new output directory |
| `--overwrite` | Replace supported single-file outputs |

Folder bundle generation requires a new or empty output directory. It does not
silently merge into an existing dataset.

## Profiling Options

| Option | Meaning |
| --- | --- |
| `--table NAME` | Override the inferred entity name for one CSV |
| `--cache-dir PATH` | Safe profile cache location |
| `--no-cache` | Force fresh folder profiling; caching is enabled by default for review-first planning |
| `--rule-sample-rows N` | Bound row-level relationship and rule mining |

Full-file schema and distribution profiling remains streaming. The rule sample
limit bounds comparisons that require row-level relationships.

## Agent Review Flow

```bash
test-data-agent agent-plan data/example_dataset \
  --workspace out/agent \
  --count 25 \
  --seed 12345 \
  --format csv

test-data-agent agent-review out/agent
# Optional; requires agent-paranoid-android[openai].
test-data-agent agent-advise out/agent --provider openai
# Advice changes the spec, so review it again.
test-data-agent agent-review out/agent
REVIEWED_SPEC_SHA256=replace-with-current-hash-from-review
test-data-agent agent-approve out/agent \
  --reviewed-spec-sha256 "$REVIEWED_SPEC_SHA256"
```

`agent-plan` must stop before generation. Review the prepared spec and manifest
context before running `agent-approve`. Add `--json` to `agent-plan`,
`agent-review`, `agent-status`, or `agent-approve` for a versioned, row-free
automation contract. Source type is detected for CSV files, CSV folders, and
safe-profile JSON; use `--source-type` to override it.

`agent-advise` is the shortest provider-backed path. It loads the optional
OpenAI adapter only when invoked, sends safe metadata through the structured
advisor contract, validates the proposal, updates the pending spec, and never
approves or generates data. Install `agent-paranoid-android[openai]`, configure
`OPENAI_API_KEY` through a secret manager, and use `--model` only when the
adapter default is unsuitable. Always run `agent-review` again after advice.

`agent-review` shows every field's type, nullability, sensitive and identifier
flags, semantic type, distribution kind, entity row count, primary key,
relationships, privacy defaults, assumptions, warnings, and the current
fingerprint. Distribution values and dataset rows are excluded. Human output
bounds long field lists and points to the complete spec. Entity and field names
are untrusted input and are escaped before terminal output.

For another provider, use the provider-neutral exchange commands:

```bash
test-data-agent agent-advisor-request out/agent \
  --exchange > advisor_exchange.json
# Use trusted_instructions, request, and response_json_schema separately.
test-data-agent agent-advisor-apply \
  out/agent advisor_proposal.json
test-data-agent agent-review out/agent
```

The request command is read-only. By default it writes one `AdvisorRequest`
JSON document. `--exchange` wraps it with package-owned trusted instructions
and the generated `AdvisorProposal` JSON Schema. The apply command accepts a
bounded regular JSON file, persists `advisor_review.json`, atomically updates
`dataset_spec.yaml`, and still stops before generation. Review the changed
spec and use the new hash reported by `agent-review`; never reuse the hash from
before advisor apply.

`agent-review` reports the SHA-256 fingerprint of the current effective spec
and an exact approval command. Record that value only after reviewing
`dataset_spec.yaml`. Approval recomputes the fingerprint immediately before
generation and fails if the file changed. Intentional edits are supported:
edit the spec, run review again, review the new hash, and approve that hash.
Successful approval writes `approval_receipt.json`.

Use `agent-status` for a short phase/next-action view and for recovery
instructions after an interrupted approval.

If approval is interrupted after the generated bundle is committed,
`agent-status` reports `recovery_required` and prints the exact recovery
command:

```bash
test-data-agent agent-recover out/agent \
  --reviewed-spec-sha256 "$REVIEWED_SPEC_SHA256"
```

Recovery revalidates the checkpoint, fingerprints, manifest, generated rows,
validation report, and source-row non-reuse before publishing missing
completion metadata. It never regenerates rows. Repeating `agent-approve` for
an already completed matching plan returns the persisted result.

## Agent JSON Contract

Use JSON output when invoking the review flow from automation or an AI client:

```bash
test-data-agent agent-plan data/example_dataset \
  --workspace out/agent --json
test-data-agent agent-advise out/agent --provider openai --json
test-data-agent agent-advisor-request out/agent \
  --exchange > advisor_exchange.json
test-data-agent agent-advisor-apply \
  out/agent advisor_proposal.json --json
test-data-agent agent-review out/agent --json
test-data-agent agent-status out/agent --json
test-data-agent agent-approve out/agent \
  --reviewed-spec-sha256 "$REVIEWED_SPEC_SHA256" --json
test-data-agent agent-recover out/agent \
  --reviewed-spec-sha256 "$REVIEWED_SPEC_SHA256" --json
```

Successful commands write one JSON document to stdout and leave stderr empty.
Planning and approval return an `AgentResult`; advisor request returns an
`AdvisorRequest` or `AdvisorExchange`; advisor apply and status return an
`AgentWorkspaceStatus`; review returns an `AgentReviewReport`. The contracts
are versioned and never include source or generated rows.

`AgentReviewReport` contains field metadata, relationships, privacy safety
flags, plan/current fingerprints, and `generation_performed: false`. It omits
distribution values and is valid only while the workspace awaits approval.

The `review` object contains `plan_id`, profile and planned/current spec
fingerprints, and `spec_changed_since_plan`. Completed results add an
`approval_receipt` tied to the exact `current_spec_sha256` supplied during
approval. Recovery status uses `next_action: "recover"` and includes the same
reviewed fingerprint without returning rows. Workspaces created before this
contract remain inspectable but must be replanned before approval.

Known argument, input, and path failures also write one versioned JSON document
to stdout when `--json` is present:

```json
{
  "schema_version": "1.0",
  "ok": false,
  "error": {
    "code": "invalid_arguments",
    "message": "the following arguments are required: --workspace",
    "command": "test-data-agent agent-plan",
    "exit_code": 2,
    "retryable": false,
    "help": "test-data-agent agent-plan --help"
  }
}
```

Stable error codes are `invalid_arguments`, `input_not_found`, `invalid_path`,
and `invalid_input`. Messages may become clearer over time; clients should
branch on `error.code`, not message text.

## Exit Behavior

| Code | Meaning |
| --- | --- |
| `0` | The command completed successfully. Running without a command also prints the starting guide and returns `0`. |
| `1` | The command completed, but dataset validation failed. This can be intentional for negative datasets. |
| `2` | Arguments, input, paths, safety checks, resources, or configuration prevented completion. |

Without `--json`, errors use concise stderr text and an exact recovery command
when contextual help is available.

For recovery steps, see [Troubleshooting](../operations/troubleshooting.md).
