# Tasks

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
