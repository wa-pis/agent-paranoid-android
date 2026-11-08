# Tasks

## 1. Baseline And Contracts

- [x] Inspect all generation, validation, writer, agent, CLI and MCP callers;
  map row/time/byte limits and distinguish them from database read budgets.
- [x] Reproduce a fictional 750k distinct rows x 25 columns workload; record
  hardware/settings/stages/conservative process-tree RSS bounds and baseline profiles.
- [x] Define typed forecast and execution policy contracts, compatibility and
  approval fingerprint rules; select the smallest eligible parallel path.

## 2. Estimates

- [x] Implement per-format low/expected/high byte estimates and assumptions.
- [x] Implement logical DB payload and optional PostgreSQL base-table model,
  explicitly excluding auxiliary storage and reporting unsupported cases.
- [x] Implement opt-in bounded synthetic calibration, versioned aggregate cache,
  stage-based time ranges and observed progress/ETA without sensitive values.
- [x] Expose shared estimate/policy behavior through Python, CLI and MCP
  planning/inspection; add schema/contract/approval tests.

## 3. Scalable Generation

- [x] Add explicit reviewed large-generation settings supporting 750k x 25;
  enforce rows/cells/time/memory/output/temp budgets without changing DB caps.
- [x] Remove measured bottlenecks and introduce bounded batch generation,
  validation and writing with atomic publication.
- [x] Implement versioned scalable deterministic streams/global key ranges;
  preserve legacy seeded fixtures and cross-worker logical identity.
- [x] Add bounded process parallelism for eligible independent-table workloads,
  exact distinctness and preflight rejection of relationships/global rules.
  Dependency-aware relational parallelism is explicitly deferred in design.md;
  the linked-table test verifies rejection and the existing bounded legacy path.
- [x] Verify cancellation, worker failure, cleanup, recovery and mandatory safety checks.

## 4. Evidence And Documentation

- [x] Run accuracy matrix and repeated 1/2/4-worker benchmarks; publish actual
  times/bytes/conservative process-tree RSS bounds, target results and limitations.
- [x] Meet >=2x 750k x 25 speedup target or explicitly revise unmet scope before
  marking performance complete; check small-workload regressions.
- [x] Update installation/usage, limits, estimate assumptions, deterministic-engine
  migration, implementation map and roadmap; use synthetic examples only.
- [x] Validate OpenSpec, focused contract/safety tests and required release checks
  on the implementation; record the final gate outcome in progress.md.
- [x] Complete independent exact-SHA review and the normal release/artifact
  acceptance process for the owner-authorized `1.7.0rc2` (2026-11-08).
