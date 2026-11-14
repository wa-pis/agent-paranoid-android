# Forecast And Generate Larger Synthetic Datasets

These additions are published in `1.7.0rc2`. They are not
available in `1.7.0rc1`. Stable 1.6.0 remains the recommended default.

## Preview Storage And Time

```bash
test-data-agent estimate-capacity dataset_spec.yaml --json
test-data-agent estimate-capacity dataset_spec.yaml --database postgresql --calibrate --json
```

The first operation uses metadata only and generates no rows. The second
explicitly creates a temporary fictional sample (default 2,000 rows per entity,
at most 5,000 rows per entity, 200,000 cells, 16 MiB output and 30 seconds).
It removes the sample and returns numeric summaries. Calibration never approves
or publishes the requested dataset and does not advance its random stream.
Calibration supports eligible linked tables with `scalable-relational-v1` in
`1.7.0rc3`. Other related or rule-constrained specs report why calibration is
unavailable.

File forecasts describe the selected CSV, indented JSON or Snappy Parquet
settings. Change `generation_settings.output_format` to compare formats.
Results include per-table and total low/expected/high bytes, separate control
artifact overhead, confidence and assumptions. They are forecasts, not safety
bounds. Metadata-only estimates have low confidence. Without calibration,
time is explicitly unknown. Calibrated time includes generation, mandatory
checks, writing and publication; scalable calibration separates their stage
costs and fixed process setup. Contention, slower storage and other settings
can invalidate timing. Legacy calibration reports end-to-end time only.
Time covers standalone bundle generation from the supplied spec. Attached-source
profiling/reuse scans and human review add uncalibrated time; these forecasts
do not measure the complete elapsed time of a source-attached agent workflow.

Database logical payload counts typed values, including UTF-8 text; it is not
a physical table-size claim. The optional PostgreSQL model approximates base
heap rows/pages with int64/float64/date/timestamp/decimal/text assumptions,
null bitmap, headers/alignment, 8 KiB pages and line pointers. Wide values
requiring uncertain TOAST storage, or integers outside int64, return unknown
physical size. Other database
engines and custom physical types are not modeled. Indexes, WAL, replicas,
backups and auxiliary storage are excluded. No database is contacted.

Explicit calibration can reuse one value-free measurement in
`.apa-capacity-measurement.json` beside the CLI spec or in the MCP workspace.
It expires after one hour; the key binds the spec, format, policy, sample size,
estimator/dependency versions and machine. Only numeric cached values are
reused. `--no-cache` / MCP `use_cache=false` forces a fresh measurement.

## Opt Into Bounded Streaming

Keep ordinary generation unchanged, or put an explicit policy in the reviewed
specification for independent tables:

```yaml
generation_settings:
  seed: 42
  output_format: csv
  execution_policy:
    engine: scalable-v1
    max_rows: 1000000
    max_cells: 25000000
    max_memory_bytes: 1073741824
    max_output_bytes: 536870912
    max_temporary_bytes: 536870912
    max_seconds: 600
    workers: 4
    batch_size: 2000
    require_distinct_rows: true
```

```bash
test-data-agent generate dataset_spec.yaml --count 750000 --output out/large
test-data-agent validate out/large/dataset_spec.yaml out/large
```

`max_rows` is the total across all tables; cells are also cumulative. The
100,000-row legacy default remains in effect without this opt-in. Source-file
profiling limits and all database read budgets remain separate and unchanged.
Existing administrator output/disk and MCP invocation limits remain additional
ceilings. The policy does not widen database or filesystem authority.

`scalable-v1` supports independent tables in valid/edge modes and CSV/JSON/Parquet.
Use Linux or macOS for scalable execution in this RC; native Windows execution
of this engine is unsupported.
Relationships, global constraints, business rules, scenarios and negative/mixed
modes reject before generation; use the legacy engine for those bounded cases.
Every table needs a synthetic-identifier primary key when distinct rows are
requested. Repeated categorical field values are allowed; whole rows remain
distinct through their key. Insufficient key pools reject. This engine never
repeats a generated batch to achieve the count.

Workers are bounded processes (1–4), with bounded batches/in-flight work.
The parent controls ordering, deadlines, writing and atomic publication.
Memory is conservatively checked at batch boundaries across parent/workers;
it is not an operating-system memory sandbox. In a long-lived Python process,
previous RSS high-water usage can also trigger admission; use a fresh process
or review a larger finite policy for that embedding. Large field/batch combinations
reject before allocation. Existing output survives failed replacement; worker
failures/deadlines reap processes and clean staging. `generation_statistics`
is a reserved entity name in this engine only.
Each serialized JSON row is limited to 4 MiB for bounded streamed recovery;
oversized rows abort before publication.

The new engine deliberately uses a new random stream. Legacy seeded output is
unchanged. Within `scalable-v1`, the same spec/seed/environment yields identical
logical rows and ordering across worker counts and batch sizes. CSV/JSON data
bytes are identical; Parquet row-group/layout metadata can differ. Manifests
record the policy/engine and include normal provenance/validation. Timing
statistics and informational progress are not deterministic data artifacts.

## Recipe: 750,000 Distinct CSV Rows

Use the scalable engine with CLI version `1.7.0rc2` or later on Linux or
macOS. Start in a fresh working directory. The synthetic integer primary
key makes every complete row distinct.

```bash
python3 - <<'PY'
import json
from pathlib import Path

fields = [{"name": "item_id", "data_type": "integer", "is_identifier": True}]
fields += [
    {"name": f"metric_{i:02}", "data_type": "integer",
     "distribution": {"kind": "numeric", "min_value": 0, "max_value": 100}}
    for i in range(24)
]
Path("large-csv.json").write_text(json.dumps({
    "entities": [{"name": "items", "row_count": 750000,
                  "primary_key": "item_id", "fields": fields}],
    "generation_settings": {
        "seed": 42,
        "output_format": "csv",
        "execution_policy": {
            "engine": "scalable-v1",
            "max_rows": 750000,
            "max_cells": 18750000,
            "max_memory_bytes": 402653184,
            "max_output_bytes": 536870912,
            "max_temporary_bytes": 536870912,
            "max_seconds": 600,
            "workers": 1,
            "batch_size": 2000,
            "require_distinct_rows": True
        }
    }
}, indent=2), encoding="utf-8")
PY

test-data-agent generate large-csv.json --count 1000 --output out/smoke
test-data-agent validate out/smoke/dataset_spec.yaml out/smoke
```

The full run requests 18,750,000 cells. The policy checks a 384 MiB process
memory budget at batch boundaries. Actual memory depends on the runtime and
schema. Run calibration on the target machine and check free space on the
filesystem that will hold the output and staging directory.

```bash
test-data-agent estimate-capacity large-csv.json --calibrate --json
test-data-agent generate large-csv.json --output out/large-csv
test-data-agent validate out/large-csv/dataset_spec.yaml out/large-csv
```

Check that `generation_manifest.json` reports `items: 750000` in
`row_counts` and that validation passes. The streamed validator verifies file
hashes and the declared key domain without loading the entire dataset.
Use `generation_statistics.json` for observed output bytes, elapsed time and
the conservative process-tree RSS upper bound.

## Recipe: Parquet For The Same Dataset

Install the [Parquet extra](../getting-started/installation.md). Change the
format in a copy of the reviewed spec and calibrate that copy. Parquet size
depends on encoding and compression.

```bash
python3 - <<'PY'
import json
from pathlib import Path

spec = json.loads(Path("large-csv.json").read_text(encoding="utf-8"))
spec["generation_settings"]["output_format"] = "parquet"
Path("large-parquet.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
PY

test-data-agent generate large-parquet.json --count 1000 --output out/parquet-smoke
test-data-agent validate out/parquet-smoke/dataset_spec.yaml out/parquet-smoke
test-data-agent estimate-capacity large-parquet.json --calibrate --json
test-data-agent generate large-parquet.json --output out/large-parquet
test-data-agent validate out/large-parquet/dataset_spec.yaml out/large-parquet
```

## Retry An Interrupted Run

For standalone `generate`, diagnose the reported budget or filesystem failure
and retry with the same spec and seed in a new output directory. Use a smaller
batch if the process reaches its memory budget. Hard termination can leave
staging files. Check that generation has stopped before removing them.

For a review-first workspace, run `agent-status`. If it reports
`recovery_required`, run `agent-recover` with the reviewed spec fingerprint
to verify the published bundle and finish completion. See
[Resource Budgets](../operations/resource-budgets.md#interrupted-publication)
for the publication and cleanup contract.

## Review And Inspect In MCP

Use `estimate_dataset_capacity(spec_path, calibrate=false)` for a saved workspace
spec. The same optional bounded calibration is available with `calibrate=true`.
`plan_dataset` accepts `execution_policy` with the fields above and stops for
human review. For CLI planning, pass the same policy as a JSON file with
`agent-plan ... --execution-policy large-policy.json`.

Planning/inspection summaries include capacity estimates. Review the exact
specification and its policy before passing `review.current_spec_sha256` to
`approve_dataset_plan`. Changing that policy invalidates old approval; changing
ETA alone does not. `inspect_dataset_plan` may include value-free progress;
it is informational and never substitutes for a completion checkpoint.
Recovery and `validate` stream scalable bundles under the approved generation
policy, without relaxing source/profiling budgets. They verify manifest hashes,
row counts, unique synthetic key ranges, schema, privacy and applicable source
reuse checks. No response contains dataset rows.
Use the bundle's effective `dataset_spec.yaml` for revalidation when generation
overrode the original counts, seed or format.

## Python

```python
from pathlib import Path
from test_data_agent.io.capacity import estimate_dataset_capacity
from test_data_agent.io.readers import load_dataset_spec
from test_data_agent import generate_dataset_bundle

spec = load_dataset_spec(Path("dataset_spec.yaml"))
forecast = estimate_dataset_capacity(spec, calibrate=True)
result = generate_dataset_bundle(spec, output_folder=Path("out/large"))
```

The in-memory `generate_dataset` operation explicitly rejects a scalable policy;
use the file-bundle API. Its optional `progress` callback receives numeric typed
progress and a final completed event after publication. See the OpenSpec change
for benchmark acceptance criteria; do not assume the same timings on other hardware.

Linux memory admission uses bounded `/proc/self/status` `VmHWM` for the current
process image, avoiding the parent memory history retained by `getrusage` across
`exec`. Missing or invalid proc metadata falls back to conservative `getrusage`
accounting; memory checks and finite policy ceilings remain enabled.


<a id="linked-tables-unreleased"></a>

## Linked Tables (1.7.0rc3)

### Recipe: Customers And Orders

Reuse the CSV recipe's execution policy with `scalable-relational-v1`.
This example requests 150,000 customers and 600,000 orders, each with a
synthetic primary key. Every order references one generated customer.

```bash
python3 - <<'PYCODE'
import json
from pathlib import Path

spec = json.loads(Path("large-csv.json").read_text(encoding="utf-8"))
spec["generation_settings"]["execution_policy"]["engine"] = "scalable-relational-v1"
spec["entities"] = [
    {"name": "customers", "row_count": 150000, "primary_key": "customer_id",
     "fields": [{"name": "customer_id", "data_type": "integer", "is_identifier": True}]},
    {"name": "orders", "row_count": 600000, "primary_key": "order_id",
     "fields": [{"name": "order_id", "data_type": "integer", "is_identifier": True},
                {"name": "customer_id", "data_type": "integer"}]},
]
spec["relationships"] = [
    {"parent_entity": "customers", "parent_field": "customer_id",
     "child_entity": "orders", "child_field": "customer_id",
     "relationship_type": "many_to_one", "confidence": 1}
]
Path("large-linked.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
PYCODE

test-data-agent estimate-capacity large-linked.json --calibrate --json
test-data-agent generate large-linked.json --output out/large-linked
test-data-agent validate out/large-linked/dataset_spec.yaml out/large-linked
```

Check the two counts separately in `generation_manifest.json` and inspect
the relationship checks in `validation_report.json`. Keep the counts in the
spec when tables have different sizes. The CLI `--count` applies to every table.

### Linked-Table Limits

Set `generation_settings.execution_policy.engine: scalable-relational-v1` to
stream related synthetic tables. Use the same finite policy fields shown above.
`scalable-v1` keeps its existing independent-table behavior.

The initial scope is acyclic many-to-one and one-to-one relationships to a
non-null synthetic integer/string parent primary key. Chains and several
parents per child are supported, with unequal table sizes and nullable child
references. For one-to-one, the child row count must not exceed its parent's,
even when some child links are null. Each table still needs a sufficient
synthetic primary-key domain when distinct rows are requested.

Parents complete before children. Up to four processes generate batches within
one table; tables themselves are not generated concurrently. Parent keys are
computed from synthetic ordinals, without retaining complete parent tables or
key sets. The engine preserves logical rows across worker and batch settings
within the same spec/seed/environment. It uses its own versioned FK stream;
legacy output and the independent engine are unchanged.

Cycles, self-links, shared primary/foreign keys, non-primary parent references,
type mismatches, conflicting active targets, global constraints, business rules,
scenarios and negative/mixed/load modes reject before staging. Rejected
relationship hypotheses do not create dependencies. Unsupported cases require
a reviewed legacy-sized run or a future implementation, with no silent fallback.

Mandatory checks prove actual PK domains/order and exact FK assignments before
publication and during streamed recovery. Relationship metrics report executed
reference/null counts even if optional relationship reporting was disabled.
Late-child failure cancels the whole staged dataset and preserves existing
output. All tables share the invocation deadline and operation/output budgets.

Bounded calibration generates the entire sampled graph, retaining valid FK
cardinality. It measures actual file sizes and apportions sampled elapsed time
by cell count for extrapolation; individual table times are approximate. Parent
barriers and small samples can make parallel ETA optimistic. The same
200,000-cell, 16 MiB and 30-second calibration ceilings apply. Metadata forecasts
flag unsupported relational execution rather than certifying it.

Python file-bundle APIs, CLI `generate`/`validate`, and MCP planning/approval/
recovery share this engine. Changing the engine changes the specification
fingerprint and requires renewed human review. Automated SDK acceptance is
technical evidence and does not represent manual client acceptance for a release.
