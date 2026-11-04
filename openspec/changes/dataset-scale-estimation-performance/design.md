# Design: Dataset Capacity And Generation Performance

## Existing Boundaries

Reuse typed DatasetSpec, core/limits.py, generation/entity_generator.py,
io/workflows.py, io/writers.py and existing application/agent services.
Inspect their current callers before implementation. Keep estimation arithmetic
and generation independent from filesystem, clocks, process pools and transports.
Do not reuse a typical-size forecast as the existing conservative safety bound.

## Forecast Contract

A typed, versioned estimate contains input/spec fingerprint, requested row counts,
format/encoding/compression settings, estimator version, method, assumptions,
low/expected/high bytes and seconds, confidence/evidence and unknown reasons.
Return per-entity and aggregate values; distinguish dataset files, control
artifacts, temporary disk, peak memory, logical DB payload and base-table bytes.
Ranges describe uncertainty, not guaranteed upper bounds. Preserve hard safety
budgets and actual incremental counters independently.

CSV accounts for headers, delimiters, quoting, escaping, newline and UTF-8 bytes.
JSON accounts for repeated property names, syntax, escaping and output layout.
Parquet accounts for schema/row groups, encoding, nulls, cardinality and selected
compression; require representative synthetic calibration or return low confidence
with wide bounds. Never infer compressed size from uncompressed CSV alone.

The default DB result is logical typed value payload, explicitly not physical
storage. An optional PostgreSQL base-table model uses explicit types, UTF-8,
null bitmap, tuple/header/alignment and page occupancy assumptions, with variable
length/TOAST uncertainty exposed. Unsupported types or engines return unknown
physical storage while retaining the supported logical estimate. No connection
is needed; no indexes, WAL, replicas, backups or auxiliary structures are included.

## Time And Calibration

Metadata-only estimation has no generation side effects. Optional calibration is
explicit, bounded by rows/cells/time/temporary bytes, generates fictional rows
from the reviewed spec, uses an isolated random stream and temporary workspace,
and never publishes a dataset or changes the real generation stream. Planning
without approval may run only explicitly requested calibration, not full generation.
Cache only value-free aggregate measurements, keyed by spec/settings fingerprint,
engine/version, machine class, workers and format; invalidate incompatible data.
Without relevant evidence, report unavailable/low confidence and the reason.

Time includes setup, generation, constraint solving, privacy/source-reuse checks,
validation, serialization and publication; estimation/calibration cost is shown
separately. Expose rows/sec and stage costs without rows or sensitive values.
During execution, progress/ETA uses observed work, a monotonic clock and bounded
updates; it must not imply completion before final validation/publication.

## Limits And Review

Retain conservative defaults for unattended clients. Introduce one explicit typed
large-generation policy with total/per-entity rows, cells, memory, output and
temporary bytes, elapsed time, workers and batch size. CLI options, Python inputs
and MCP planning must resolve to the same policy; document precedence with existing
environment defaults. At least 750,000 x 25 must be expressible without hidden
configuration. A forecast over budget returns the failing dimension and a concrete
bounded remedy. Never automatically raise limits from an optimistic estimate.

Record semantic generation settings, uniqueness policy and accepted execution
policy in the reviewed plan/receipt. A change in counts, spec or accepted budgets
requires renewed review; volatile ETA/progress measurements do not invalidate
approval. Worker/batch changes cannot change generated rows under the new engine.
Changes outside the approved execution policy require review. Inspect/recovery
retain plan identity, actual counters and actionable failure states.

## Performance Strategy

1. Capture a repeatable baseline with synthetic 25-column specifications and
   profile CPU, validation scans, allocation, serialization and IPC separately.
2. Remove verified repeated work before adding concurrency. Preserve every check.
3. Generate/write bounded batches without materializing the entire dataset;
   account for relationship/key pools, uniqueness state and validation indexes.
   Unsupported global rules must use a bounded fallback or fail before generation.
4. For eligible independent row work, use bounded processes (not CPU-bound Python
   threads by default). Parent owns policy, ordering, progress and publication;
   workers receive immutable safe specs and bounded tasks. Cap in-flight batches,
   cancel on failures/timeouts, terminate/reap children and clean staging files.
5. Use deterministic entity/row/field substreams and global synthetic key ranges;
   workers and batch size must not cause duplicates, key collisions or reordered
   output. Relationships follow a dependency-aware schedule, not arbitrary splits.

Changing random stream semantics can change historical seed output. Keep the
legacy engine as the default compatibility path; make the scalable engine explicit,
record its version in manifests and document that determinism is scoped to engine
version/spec/seed. Verify existing legacy golden fixtures remain unchanged.
Within the scalable engine, worker counts and chunk sizes yield identical logical
rows and ordering. Byte identity is required for deterministic CSV/JSON settings;
Parquet logical identity is required, with encoding/library metadata documented.
Never use copied source rows or repeat a completed synthetic batch for speed.

## Acceptance Matrix

- Small CI fixtures cover integer/decimal/date/time, nulls, long/Unicode/escaped
  strings, high/low cardinality, keys, parent-child relations, formulas, valid,
  negative and mixed modes. Unsupported combinations fail explicitly.
- Dedicated offline benchmark: 10k, 100k and 750k rows x 25 fields, plus a bounded
  linked-table case; explicit seeds, storage, CPU/RAM/OS/Python/library versions,
  cold/warm cache conditions, >=3 repeats and median/range recorded. Baseline and
  optimized runs use the same host, fixture, validation and output settings.
- For calibrated supported fixtures above 10k rows, measured CSV/JSON size must
  fall in forecast bounds with expected relative error <=25%; Parquet <=40%.
  Measured end-to-end time must fall in bounds with expected relative error <=40%
  on the same unloaded host/settings. Bounds wider than 3x must be labeled low
  confidence, not counted as accurate. Unsupported/noisy cases report uncertainty.
  Database formula tests use independently derived layouts; physical PostgreSQL
  calibration may use a disposable local synthetic instance only, never live data.
- Performance target: >=2x median total speedup on the simple 750k x 25 fixture
  versus baseline on a >=4-core reference host; show actual 1/2/4-worker scaling.
  Small 10k-row serial work must not regress >15% under repeated controlled runs.
- Show peak RSS for the whole process tree and temporary-disk high-water marks.
  Memory stays within the approved policy as row count grows; account for any
  inherently growing uniqueness/relationship state rather than claiming O(1).
- Validate 750k distinct complete rows using a synthetic unique key, exact counts,
  no overlapping worker ranges, relationship integrity, privacy and source reuse.
  Requested uniqueness with insufficient domain capacity fails before publication.
- Fault tests cover worker crash, disk full, deadline, cancellation and stale
  approval; no partial final bundle, orphan process or overwritten existing output.

## Delivery

Additive Python/CLI/MCP estimate fields/tools with frozen-contract updates and
bounded summaries; no dataset rows in responses. Update user docs, implementation
map and roadmap together with implementation. Larger benchmarks run explicitly
or in a dedicated job rather than burdening every unit test. Benchmark results
are release evidence; do not prefill invented measurements. Final release needs
normal independent review and release gates; no version is selected by this plan.
