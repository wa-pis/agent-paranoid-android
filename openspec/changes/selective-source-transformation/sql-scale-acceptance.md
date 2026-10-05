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
