# Agent Design

The agent layer is a safe orchestration boundary over the existing deterministic
pipeline. It plans work, writes review artifacts, waits for approval, and then
calls deterministic generation and validation code.

The agent does not generate rows with an LLM. It does not receive unrestricted
SQL access, shell access, or raw production rows.

PlantUML diagrams for this layer are available in:

- [Agent Workflow](architecture_agent_workflow.puml)
- [Safety Boundaries](architecture_safety_boundaries.puml)

## Flow

```text
User or AI client
  -> agent-plan
    -> safe CSV/profile profiling
    -> DatasetSpec inference
    -> profile.json / dataset_spec.yaml / agent_plan.json
    -> stop for review
  -> agent-status
    -> validate workspace state
    -> report phase, next action, artifact paths, and safe summary
  -> agent-approve
    -> deterministic synthetic generation
    -> source-row reuse checks when source CSV is available
    -> validation_report.json / generation_manifest.json
```

## CLI Usage

Plan from a CSV folder and stop before generation:

```bash
test-data-agent agent-plan tests/fixtures/example_dataset \
  --workspace out/agent \
  --count 25 \
  --seed 12345 \
  --format csv
```

Review `out/agent/dataset_spec.yaml`, then approve:

```bash
test-data-agent agent-status out/agent
test-data-agent agent-approve out/agent
```

Inspect the same workspace as versioned JSON for automation or an AI client:

```bash
test-data-agent agent-status out/agent --json
```

Status inspection is read-only. It rejects incomplete or contradictory
workspace state and never returns source or generated rows.

Plan from one CSV file:

```bash
test-data-agent agent-plan tests/fixtures/customers.csv \
  --workspace out/customer_agent \
  --table customers \
  --count 25 \
  --seed 12345 \
  --format csv
```

Plan from a safe profile JSON:

```bash
test-data-agent agent-plan examples/orders_profile.json \
  --workspace out/profile_agent \
  --count 25 \
  --seed 12345 \
  --format json
```

`agent-plan` detects CSV files, folders containing CSV files, and validated
safe-profile JSON. Use `--source-type` only as an explicit override.
DatasetSpec JSON or YAML belongs to the existing `generate` workflow.

## Artifacts

Planning writes:

- `agent_request.json`
- `agent_plan.json`
- `profile.json`
- `dataset_spec.yaml`

Approval writes:

- `agent_result.json`
- `generated/<entity>.csv|json|parquet`
- `generated/profile.json`
- `generated/dataset_spec.yaml`
- `generated/validation_report.json`
- `generated/generation_manifest.json`

## Result Contract

The Python API returns an `AgentResult`. Its `summary` is one of two typed
models:

- `AgentPlanSummary` reports entities, relationship and constraint counts,
  seed, and output format while approval is pending.
- `AgentGenerationSummary` reports row counts, seed, output format, validation
  status, and the `synthetic` and `source_rows_copied` safety facts.
- `AgentWorkspaceStatus` reports the current phase, next action, artifacts, and
  the applicable typed summary. Its JSON contract has `schema_version: "1.0"`.

The same fields are serialized under `summary` in `agent_plan.json` and
`agent_result.json`. Existing dict-style reads such as
`result.summary["row_counts"]` remain supported, but new Python integrations
should use typed attributes such as `result.summary.row_counts`.

## LLM Responsibilities

An LLM-based client may:

- choose `csv`, `csv-folder`, or `profile` source type;
- call `agent-plan`;
- summarize the inferred `DatasetSpec`;
- ask a human to approve or edit the spec;
- call `agent-approve` after approval;
- report manifest and validation summaries.

An LLM-based client must not:

- generate rows itself;
- bypass `DatasetSpec`;
- use arbitrary SQL;
- return raw rows or raw PII in chat;
- treat free-form reasoning as validation.

## Safety Boundary

The Python workflow still enforces the important invariants:

- profile safety checks reject unsafe sensitive distributions;
- CSV source-row reuse checks run before output is committed;
- generation is deterministic by seed;
- generation folders are assembled through temporary folders;
- validation reports and generation manifests are written for every approved
  generation.
