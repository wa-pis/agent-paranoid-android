# Tasks

- [x] Keep small/low-cardinality distinct sets and implement the per-entity
  one-pass handoff after 1,000,000 summed field entries, preserving inference.
- [x] Add lazy keyed Arrow counting with fixed SQL, native query deadlines,
  private bounded spill and value-free backend/cleanup failures.
- [x] Add the optional profiling extra, reviewed lock/constraints, dependency
  inventory, isolated wheel profiles and focused minimum-dependency CI jobs.
- [x] Document the unreleased install, module boundary, operational limits and
  release-candidate requirement without claiming a stable release.
- [x] Verify complete safe-profile/spec/fingerprint/cache equality for set and
  DuckDB paths, including handoff boundaries, late duplicates and source order.
- [x] Exercise real spill privacy, permissions, success/error/cancellation
  cleanup, disk/resource limits, native deadline and no partial cache.
- [x] Run focused integration, dependency, contract and documentation checks,
  Ruff, strict typing and the final relevant regression suite; record results.

Packaging evidence already collected: 53 focused dependency/release-artifact
tests, Ruff, lock freshness and compatibility checks passed. Only DuckDB 2.0.1
was added to the lock; existing versions were preserved. Isolated base and
profiling minimum wheel installs passed demo/CSV/JSON checks; the profiling
environment used DuckDB 2.0.1 and PyArrow 15.0.0, with 12 approved licenses.
The final runtime wheel and minimum-version behavior were subsequently verified;
see [validation.md](validation.md) for 24 full-profile comparisons, real spill and
SIGINT evidence, 1,886 passing regression tests, 91.33% coverage and the final
wheel identity. These local checks are not release acceptance.
