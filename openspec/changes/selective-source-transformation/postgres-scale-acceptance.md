# Private PostgreSQL-result scale acceptance — 2026-09-29

## Scope and candidate

Installed development wheel, fictional injected driver, actual private spawned
capture worker → captured-source profiling → saved-policy review → temporary
CSV publication → full ordered readback and cleanup. No product monkeypatch,
database connection, external API, receipt creation or public activation.
The fixture does not execute SQL against PostgreSQL and is not live-driver
performance evidence. Source-free generation/profiling/MCP budgets are unchanged.

- Base: `637065966c12584e11c9b437c1e8b8f8d708c0df`; candidate code is this PR.
- Development wheel version `1.5.0`, NOT a published release candidate.
- Wheel SHA-256: `db2a70a56be0b474b3a0898acce7a68bbcd5cdb1ed51bfbfd05d0b1e72593681`.
- Harness: `scripts/accept_transformation_postgres_scale.py`.
- Harness SHA-256: `5a1a8e9ef75271f26c75cf103282f8bb0fe89464914108a042d6663149f0be5a`.
- Python 3.11.2, Darwin arm64; installed import path verified under
  `/private/tmp/apa-postgres-scale-wheel.byRzye/installed/test_data_agent/`.

## Reproduction and bounds

Build a wheel, install it using `uv pip install --no-deps --target <wheel-target>`
with dependencies already available, then run:

```sh
PYTHONPATH=<wheel-target> python scripts/accept_transformation_postgres_scale.py --rows 300000 --columns 50
```

Saved profile selects 1M rows, 100 columns, 100M cells, 64MiB encoded input,
512MiB expanded input and output. Run capture selects 300,000 rows and 64MiB;
overall file/output budgets are 512MiB, review 1MiB, elapsed budget 1800s.
No implicit increase or truncation. Profiling defaults remain 10,000 result
rows and 100,000 result cells; they do not govern transformation capture.

The local driver returns alternating fictional text rows through a named,
forward-only cursor with requested read-only transaction settings. Every field
uses explicit inline replacements. Assertions cover every output cell, exact
row count/order, headers, 100% replacement provenance, mixed-origin label,
source digest, child reaping, cursor/connection close and rollback, temporary
publication and fixture-directory cleanup. No source preservation is requested.

## Result

**Passed: 300,000 × 50 = 15,000,000 cells in 217.623 seconds.**

- Captured envelope: 2,730,386 bytes; capture completed at 13.397s.
- Profile completed at 63.401s; review completed at 112.726s.
- Output CSV: 90,000,450 bytes; all rows and columns read back and checked.

The initial 1,000 × 50 smoke exposed one Parquet row group per fetched row:
7,518,430 captured bytes, 3.056s end to end. Bounded batching reduced the same
fixture to 25,653 bytes and 1.342s. Fetch size stays one; strict scalar/type
checks precede buffering. Flush occurs at 1,024 rows or a conservative 1MiB
payload estimate. This is not a hard RSS/wire-allocation guarantee.

Focused capture/worker regressions: 66 passed, including a 2,049-row ordered
three-group capture and invalid final-row rejection with cleanup. Existing
typed overflow/session recovery and requested-vs-observed tests remain covered.
Full offline milestone suite: 2,567 passed, 10 live-service cases deselected,
coverage 90.98% (85% required), 118.56s. Ruff, mypy (135 source modules),
compileall, strict OpenSpec/MkDocs and whitespace checks passed. All 133 Python
files packaged in the tested wheel match candidate source bytes exactly.

Remaining: public interface/activation review, other format routes and 1M ×100
target acceptance, client evidence reconciliation and final RC gates. This
private fictional checkpoint does not close those requirements. The previously
accepted unchanged CSV-scale scenario was not repeated.

## Configurable target harness — 2026-10-05

The fictional-driver harness accepts `--max-bytes`, `--capture-bytes` and
`--max-seconds`, retaining historical 512MiB / 64MiB / 1800s defaults.
Per-file capture, total-input, decoded-input, output and worker time budgets are
explicit; ordinary PostgreSQL profiling row/cell limits remain unchanged.
10 × 3 smoke passed at 2MiB / 1MiB capture / 60s, including worker lifecycle,
full readback and cleanup. Six invalid-budget startup checks and Ruff passed.
This is harness validation, not target proof or live database evidence.

Initial target run FAILED before capture: candidate
`a14df8866b1ef4dbe5ac3d6d27959c94ee22a447`, installed wheel SHA-256
`bcce6365fbb6724d2d583796a61567d99bbdc6c9a9e86eb7e02a5d65f156ae8e`
(same runtime wheel as b49ceed; these commits change harness/docs only).
Arguments: `--rows 1000000 --columns 100 --max-bytes 1073741824
--capture-bytes 134217728 --max-seconds 3600`.
Resumable state: `/private/tmp/apa-postgres-target-current.json`; PID 80533;
log `/private/tmp/apa-postgres-target-a14df88-333utbsh/run.log`.
The generated name field_cc was correctly classified as sensitive before
opening the fictional stream. Fixture correction uses neutral numeric suffixes
and checks all names against the existing classifier; no runtime guard changed.
No live DB, public activation or all-route/RC clearance is implied.

Corrected 10 × 100 smoke passed at target budgets (0.693s), including full
readback and lifecycle/cleanup. **Corrected target PASSED:**
SHA `611b78178fea285b193fb3bc92dccdc2bd6a953a`, same installed runtime wheel above; immutable copied
harness SHA-256 `522f638f67bb9c0ee1c66df8a0d5dfc1b0d174ad95960a6541384e5f0684bafa`.
State `/private/tmp/apa-postgres-target-current.json`, PID 80658,
log `/private/tmp/apa-postgres-target-611b781-5gvohx2q/run.log`. Poll this run before launching another.

Target results: capture 81.850s / 35,469,307 encoded bytes; profile cumulative
401.913s; review cumulative 724.378s; complete 1412.882s. Output CSV
600,001,000 bytes. All 100,000,000 cells passed ordered readback, exact row
count, 100% replacement provenance, unchanged captured digest and input/output
cleanup; child lifecycle and no remaining worker assertions passed.
Profiling limits remain 10,000 rows / 100,000 cells; explicit transformation
limits admitted 1M rows / 100M cells. This is the fictional injected-driver
private PostgreSQL-result → CSV route only, not live DB or public/all-route RC
acceptance. The terminal JSON remains in the log above.

## Remaining output harness checks — 2026-10-05

The same fictional worker fixture now accepts `--output-format parquet` or
`postgresql_sql`. 2051 × 3 multi-batch readback smokes passed: Parquet 0.493s
/ 2,037 bytes; SQL full framing/every ordered INSERT/COMMIT/EOF checked without
execution. Both retain schema/provenance/digest/lifecycle/cleanup assertions.
Ruff passed. Harness time validation matches the existing isolated worker's
0.1..3600s range before fixture creation. Target checks for these two outputs
remain open. Do not start another large run while the recorded Parquet →
Parquet target is still active.
