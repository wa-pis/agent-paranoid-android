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
Related/rule-constrained calibration is currently unsupported and reports why.

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
it is not an operating-system memory sandbox. Large field/batch combinations
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
