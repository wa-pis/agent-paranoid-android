# Fictional SQL-result scale harness

`scripts/accept_transformation_postgres_scale.py` retains PostgreSQL as the
default. `--adapter trino` supplies 1024-row fictional Arrow batches to the
existing `_capture_authorized_result` boundary. It verifies adapter/table/column
identity, explicit projection/LIMIT, complete supplied row count and stream
cleanup. The query is parsed and authorized before the trusted stream opens.
There is no Trino connection, server SQL execution, network adapter or isolated
Trino worker in this fixture. It establishes only supplied-result authorization,
bounded encoding, review and private publication/readback. This does not prove
network cancellation, server budgets or public route activation.

The same explicit saved/run row/cell/file/decoded/output/capture/time ceilings
apply. PostgreSQL retains its actual isolated worker and unchanged ordinary
profiling limits. No source values or credentials are used beyond locally
created fictional alpha/beta fixtures.

2026-10-05: three Trino-mode 2051 × 3 smokes passed through CSV, Parquet and SQL
artifact outputs (0.147s / 0.155s / 0.158s), including full readback, provenance,
digest and cleanup. PostgreSQL-mode CSV compatibility smoke passed (0.437s),
including child lifecycle checks. Ruff and whitespace checks passed. Large
Trino-result target proofs remain open; no all-route or RC clearance.

Do not launch another large target while the recorded Parquet → SQL run in
`csv-scale-acceptance.md` is active. Poll its retained log first.

## Sequential target queue — result pending

Exact fixture candidate `b249699ab16f8aad7f220acb16542d505f9b4edf`; unchanged installed runtime wheel
15cd2d4, SHA-256 `f2bf7d5dfb90e328ada721e72acc74515b18ba565d0c07c745806e957fdc12eb`.
Copied harness SHA-256 `93a3d8d38293b8c42a9e9996c327fc7fd4fbd96b5aa2ae33f949b5e9070cf0af`; runner SHA-256
`2324997a5b640b3eefd4c7d8e020e56f5004433fe9c5f7f36e8d737fd098027f`. State pointer
`/private/tmp/apa-remaining-target-queue-current.json`; root `/private/tmp/apa-remaining-target-queue-xqs_7uxi`;
runner PID 84062. Five remaining supplied SQL-result targets run sequentially:
PostgreSQL → Parquet/SQL, then fictional Trino result → CSV/Parquet/SQL.
Each uses 1M × 100, explicit 128MiB capture, 1GiB output/file (3GiB for SQL)
and 3600s. It waits for the recorded Parquet → SQL terminal pass and stops at
first failure. Read state.json and per-job logs before starting any new run;
never duplicate an active or passed stage. No tests are claimed passed yet.
No live DB/network adapter, public/RC activation, new source audit or release
gate clearance is implied.

Queue checkpoint 2026-10-05: prerequisite Parquet → SQL terminal pass retained
(3398.476s / 100M cells). Queue state is running `postgres-parquet`, child
PID84146, no completed queue stages yet. Do not start another large target.
Current complete private matrix is 7/12; no final release clearance.

2026-10-05 queue checkpoint: PostgreSQL → Parquet target PASSED (candidate
b249699 / recorded immutable wheel+harness above): 1M × 100, 100M cells,
35,469,307 captured bytes, 17,493,375 output bytes, complete1602.427s.
All typed ordered readback, 100% replacement provenance, input digest, child
lifecycle and temporary cleanup assertions passed. Ordinary profiling caps
remain10,000rows/100,000cells. Per-job log: postgres-parquet.log under the
queue root. Current private matrix8/12. Queue advanced to
postgres-postgresql_sql, child PID84733. Poll retained state; no duplicate runs.
