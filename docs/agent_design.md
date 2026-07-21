# Agent Design

The agent layer is a safe orchestration boundary over the existing deterministic
pipeline. It plans work, writes review artifacts, waits for approval, and then
calls deterministic generation and validation code.

The agent does not generate rows with an LLM. It does not receive unrestricted
SQL access, shell access, or raw production rows.

## Flow

```text
User or AI client
  -> agent-plan
    -> safe CSV/profile profiling
    -> DatasetSpec inference
    -> profile.json / dataset_spec.yaml / agent_plan.json
    -> stop for review
  -> agent-approve
    -> deterministic synthetic generation
    -> source-row reuse checks when source CSV is available
    -> validation_report.json / generation_manifest.json
```

## CLI Usage

Plan from a CSV folder and stop before generation:

```bash
test-data-agent agent-plan tests/fixtures/example_dataset \
  --source-type csv-folder \
  --workspace out/agent \
  --count 25 \
  --seed 12345 \
  --format csv
```

Review `out/agent/dataset_spec.yaml`, then approve:

```bash
test-data-agent agent-approve out/agent
```

Plan from one CSV file:

```bash
test-data-agent agent-plan tests/fixtures/customers.csv \
  --source-type csv \
  --workspace out/customer_agent \
  --table customers \
  --count 25 \
  --seed 12345 \
  --format csv
```

Plan from a safe profile JSON:

```bash
test-data-agent agent-plan examples/orders_profile.json \
  --source-type profile \
  --workspace out/profile_agent \
  --count 25 \
  --seed 12345 \
  --format json
```

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
