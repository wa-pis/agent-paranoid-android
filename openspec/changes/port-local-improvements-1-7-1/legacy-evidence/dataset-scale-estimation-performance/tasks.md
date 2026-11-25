# Tasks

## Completed Exact-Distinct Experiment

- [x] Compare Python set, SQLite and table/streaming DuckDB using bounded
  synthetic digest batches at 10k/100k/750k rows x 25 columns, high/low
  cardinality and three repeats; record exact counts, time, RSS and scratch.
- [x] Publish raw measurements and the decision in
  [distinct-benchmark-evidence.md](distinct-benchmark-evidence.md); select
  streaming DuckDB for a future large high-cardinality path while retaining
  the current Python default. Runtime integration and full profiling acceptance
  remain outside this completed component experiment.

## First Generation Acceleration (Implemented, Unreleased)

- [x] Prepare typed distributions once per entity and call in generation and
  schema validation; retain the seeded random stream and all safety checks,
  with no shared cache between invocations.
- [x] Publish repeated before/after measurements of the implemented optimization
  in [generation-distribution-evidence.md](generation-distribution-evidence.md).
  This does not complete the broader forecast, batching or parallelism tasks.

## Initial Python Parallel Path (Implemented, Unreleased)

- [x] Add an opt-in typed Python process adapter with explicit row/cell/time
  bounds, at most four workers and one logical tile per worker in flight.
- [x] Add `tiled-v1` fixed 4,096-row seed streams and ordered collection; retain
  legacy defaults and reuse global constraint/privacy/schema validation.
- [x] Document Python-only scope, engine migration, complete-dataset memory,
  unsupported semantic callbacks and remaining workflow/publication integration.
- [x] Publish repeated 1/2/4-worker measurements at 100k and 750k x 25,
  including seeded equality and concurrent process-tree peak RSS in
  [parallel-generation-evidence.md](parallel-generation-evidence.md).
- [x] Complete fault, cancellation and independent review evidence for this path
  in [parallel-generation-evidence.md](parallel-generation-evidence.md).
  These steps do not complete the broader forecast, streaming or release tasks.

## Streaming Backend Experiment (Benchmark Only)

- [x] Compare common four-worker `tiled-v1` / Arrow generation with Python-key
  tracking and with DuckDB storage/global-key checks at 100k and 750k x 25.
- [x] Preserve mandatory batch privacy/schema validation, global key/count
  checks, safe CSV encoding and bounded process lifecycle; reject unsupported
  global rules before generation and test failure/temporary-file behavior.
- [x] Publish three repeated measurements per backend/size, coordinator stages,
  concurrent process-tree RSS and exact seeded CSV equality against the full
  materialized reference in `streaming-generation-evidence.md`.
  This experiment does not implement a public streaming export API.

## 1. Baseline And Contracts

- [ ] Inspect all generation, validation, writer, agent, CLI and MCP callers;
  map row/time/byte limits and distinguish them from database read budgets.
- [ ] Reproduce a fictional 750k distinct rows x 25 columns workload; record
  hardware/settings/stages/peak process-tree memory and baseline profiles.
- [ ] Define typed forecast and execution policy contracts, compatibility and
  approval fingerprint rules; select the smallest eligible parallel path.

## 2. Estimates

- [ ] Implement per-format low/expected/high byte estimates and assumptions.
- [ ] Implement logical DB payload and optional PostgreSQL base-table model,
  explicitly excluding auxiliary storage and reporting unsupported cases.
- [ ] Implement opt-in bounded synthetic calibration, versioned aggregate cache,
  stage-based time ranges and observed progress/ETA without sensitive values.
- [ ] Expose shared estimate/policy behavior through Python, CLI and MCP
  planning/inspection; add schema/contract/approval tests.

## 3. Scalable Generation

- [ ] Add explicit reviewed large-generation settings supporting 750k x 25;
  enforce rows/cells/time/memory/output/temp budgets without changing DB caps.
- [ ] Remove measured bottlenecks and introduce bounded batch generation,
  validation and writing with atomic publication.
- [ ] Implement versioned scalable deterministic streams/global key ranges;
  preserve legacy seeded fixtures and cross-worker logical identity.
- [ ] Add bounded process parallelism for eligible workloads, dependency-aware
  execution, exact distinctness and bounded fallback/rejection for global rules.
- [ ] Verify cancellation, worker failure, cleanup, recovery and all safety checks.

## 4. Evidence And Documentation

- [ ] Run accuracy matrix and repeated 1/2/4-worker benchmarks; publish actual
  times/bytes/whole-process memory, target results and limitations.
- [ ] Meet >=2x 750k x 25 speedup target or explicitly revise unmet scope before
  marking performance complete; check small-workload regressions.
- [ ] Update installation/usage, limits, estimate assumptions, deterministic-engine
  migration, implementation map and roadmap; use synthetic examples only.
- [ ] Validate OpenSpec, focused contract/safety tests and required release checks
  on final implementation; independent review before any separately authorized release.
