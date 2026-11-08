# Progress — Dataset Capacity And Generation Performance

## 2026-11-08 — Implementation And Measured Acceptance

The owner authorized implementation with “давай смотреть и делать”. Work is
isolated in `codex/dataset-scale-estimation`, based on current main
`0014efa4b652c26573447734330f405918d6e13b`; the original checkout's unrelated
edits were preserved. OpenSpec commit `c84482d31e0d88e81caa6cf57672a940bf041059`
was already pushed. This change does not resume the historical RC2 automation,
activate source preservation or authorize a new package release.

### Implemented

- Typed metadata forecasts for CSV/JSON/Snappy Parquet and logical/approximate
  PostgreSQL row storage, with ranges, assumptions, unknown layouts and safe
  budget remedies. Shared CLI `estimate-capacity`, Python and workspace MCP
  `estimate_dataset_capacity`; metadata-only planning remains non-generating.
- Explicit bounded synthetic calibration: 100–5,000 rows/entity, 200k cells,
  16 MiB output, 30-second child-process ceiling, private cleanup and numeric-only
  one-hour cache reuse. Fixed Parquet startup extrapolation after an accuracy
  failure; duration scope explicitly excludes attached-source scans/human review.
- Explicit reviewed `scalable-v1` policy; total rows/cells, time, disk, memory,
  1–4 processes and bounded batches. Source/database/transport limits remain
  separate. Scoped metadata reuse removes measured privacy/distribution hotspots
  while preserving per-cell checks and legacy golden data.
- Fresh row-local random streams, disjoint synthetic key domains, exact counts
  and distinct complete rows; streamed writing, validation and atomic bundles.
  Typed informational progress, real SDK stdio approval/replay/recovery tests.
  Policy changes invalidate the prior reviewed fingerprint. Generated bundles
  are rechecked without borrowing source/profiling allocation allowances.
- Cancellation, worker/deadline/disk failures and child cleanup; duplicate keys,
  unsafe content, untracked artifacts and control-file name collisions reject.
  JSON writer/recovery share a bounded 4 MiB serialized-row contract.
- Documentation, schemas and additive frozen contracts updated. A new contract
  overlay preserves reversible historical transformation activation patches;
  no historical approval gate is weakened or reinterpreted.

### Evidence

See [evidence.md](evidence.md) and [numeric measurements](benchmark-evidence.json).
Three 750k × 25 runs/configuration: baseline median 138.161 seconds; scalable
1/2/4 workers 50.490 / 31.514 / 18.557 seconds (**7.45×** at four workers).
Maximum conservative whole-process RSS upper bound at four workers: 373.56 MiB,
under 1 GiB policy. Small unchanged legacy path improves from 1.830 to 0.904
seconds at 10k; no measured small-run regression.

Twelve calibration/format/type cases at 10k and 100k passed their bounds and
accuracy targets: maximum size error 0.69%, duration error 22.01%. Separate
full streamed revalidation of 750k distinct rows × 25 fields passed in 20.31
seconds. These are fictional local development measurements; the user's
20-minute run and live database/provider performance were not reproduced.
Six default legacy-engine accuracy cases also passed (maximum size error
2.28%, duration error 13.81%). Effective load-test sample counts are covered
separately. SDK 1.28.1 passed eight isolated compatibility tests; SDK 2 uses
the locked development environment. The latest capacity-focused run passed
all 43 tests, including seed, row-size, file-name and shared serial-deadline
boundaries. Serial batches share the parent's invocation deadline rather than
restarting a fresh allowance for each batch.

### Scope And Checks

The first scalable engine supports independent tables in valid/edge modes.
Relationships, global/native/business rules, scenarios and negative/mixed/load
test modes reject before publication; the bounded legacy path is retained and
tested. Relational parallel speedup and OS-enforced hard-RSS limits are not claimed.
PostgreSQL storage is an assumed layout, with no physical server calibration.

Strict OpenSpec validation, strict MkDocs build, lint/type checks and focused
real SDK/contract/safety tests passed during implementation. The first full
release-check run reached 91.82% coverage, with 4,847 passed and 23 skipped;
eight existing controlling-TTY acceptance tests failed in the restricted test
environment. A rerun with normal terminal access passed all release checks:
4,857 passed, 23 skipped, 91.80% coverage. The next full run passed with the
legacy calibration and entry-point boundary checks (4,866 passed, 23 skipped,
91.88%). The final run includes the shared serial-deadline regression and
passes the complete gate: **4,867 passed, 23 skipped, 91.88% coverage**.
Lint/types/compile, dependency licenses/compatibility, privacy boundaries,
operational budgets, both schema freshness checks and quickstart all passed.
Strict OpenSpec and MkDocs checks also passed. The 23 skipped tests do not
establish live database/provider acceptance; no such access was attempted.
All terminal receipts/approvals in tests use fictional
fixtures and are not human dataset acceptance evidence.

Implementation checks are complete. The delivery commit contains this log,
the executable change and its evidence on `codex/dataset-scale-estimation`.
Remaining release review/acceptance needs a separately authorized release.
No public package, tag or container has been published by this change.

## 2026-11-08 — RC2 Release Preparation

The owner separately authorized a PR, merge after green checks and publication
of the next RC. The latest published candidate is 1.7.0rc1; the selected next
version is 1.7.0rc2. Version metadata and the changelog are prepared. Required
independent exact-SHA review, exact-main workflows, Ubuntu artifact preflight,
signed acceptance and public verification remain pending; none is claimed.
