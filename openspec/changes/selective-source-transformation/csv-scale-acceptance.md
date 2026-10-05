# Private CSV scale acceptance — 2026-09-28

## Scope and candidate

This checkpoint tests the private, replacement-only CSV route. It does not
activate public execution, approve preservation, test private client data,
certify all 12 routes, or publish 1.6.0rc1.

- Base: `737268d8e92b2876deb71fc035685bd3a3b01859`; candidate is this PR's code.
- Local development wheel retains version `1.5.0`; it is NOT a released RC.
- Wheel SHA-256: `6f93cd68e938c56bde1033fef58758290c4f80f29c723459f6063bf0b66bbceb`.
- Runtime: Python 3.11.2, Darwin arm64. Installed wheel import location verified
  under `/private/tmp/apa-csv-scale-wheel.pcVR7P/installed/test_data_agent/`.
- Harness: `scripts/accept_transformation_csv_scale.py`; no product monkeypatch,
  external API/database, supplied private input, or approval receipt.

## Reproduction

Build the candidate wheel with the pinned hatchling backend, install it into
an isolated target using `uv pip install --no-deps --target <wheel-target>`
(dependencies must already be present), then run:

```sh
PYTHONPATH=<wheel-target> python scripts/accept_transformation_csv_scale.py --rows 300000 --columns 50
```

Only fictional temporary inputs and outputs are created. The saved YAML
profile explicitly selects 1M rows, 100 columns, 100M cells and 512MiB input/output
ceilings. Total input/output run budgets are 512MiB; review is 1MiB and elapsed
work is bounded by 1800 seconds. No implicit budget escalation.

The fixture alternates two fictional row patterns. All 50 fields have explicit
replacement actions; global CSV mappings and one column override exercise
precedence and a non-cascading target. Full readback checks every row and column,
exact row count/order, mixed-origin manifest, 100% replacement provenance,
unchanged input digest, and temporary-input/output cleanup.

## Results

**Passed: 300,000 rows x50 columns =15,000,000 cells**, through installed-wheel
profile → saved-policy/file review → private temporary publication → complete
readback and cleanup. CSV output:90,150,450 bytes. Elapsed:272.572s (~4m33s).
All row/column, mapping, manifest/provenance, input-digest and cleanup assertions
passed. This establishes this fictional private CSV scenario, not arbitrary
data widths, peak-memory containment, public activation or the1M x100 target.

Small harness smoke (10 x3): passed in 0.029s. This only validates the harness.
Candidate full-run cumulative stage timings: profile68.522s, review135.900s.

## Regression gates

- Full offline suite: 2557 passed; two release-fixture tests initially failed
  because subprocess `git` resolved to Apple's unavailable system Git.
  Retried only those two with `/opt/homebrew/bin` first in PATH: passed.
  Ten live-service integration tests deselected, not claimed passed.
- Coverage: 90.99%, required 85%.
- Ruff: source, tests and scripts passed. Mypy: all135 source files passed.
- Compileall, OpenSpec strict and diff whitespace checks passed.

Residual work: SQL-result capture/worker budget propagation, public interface
and activation review, full target1M x100/multi-route acceptance, documentation
and final RC release gates. No hard RSS/wire guarantee is claimed.

## Configurable target harness — 2026-10-05

The CSV harness now accepts explicit `--max-bytes` and `--max-seconds`,
retaining 512MiB / 1800s defaults. The selected byte budget applies both to
saved per-file/total-input/output limits and to run limits. Invalid nonpositive,
nonfinite time or oversized integer budgets fail before fixture creation.
Small synthetic 10 × 3 scenario passed with 1MiB / 60s, plus five invalid-budget
startup checks and Ruff. This is harness validation, not measured target proof.
For 1M × 100, this fixture's CSV source is 550,000,900 bytes and replacement
output is 600,500,900 bytes; both exceed 512MiB. Use an explicit sufficient
byte budget instead of treating row/cell configuration as a byte-limit override.

**Target run PASSED:** exact installed runtime
`b49ceed5fc3d64698f4cfd4135b2958edd915512`, wheel SHA-256
`bcce6365fbb6724d2d583796a61567d99bbdc6c9a9e86eb7e02a5d65f156ae8e`.
Command: `--rows 1000000 --columns 100 --max-bytes 1073741824 --max-seconds 3600`.
Local resumable state: `/private/tmp/apa-csv-target-current.json`;
log: `/private/tmp/apa-csv-target-b49ceed-xi8v0xap/run.log`; PID 80161.
Profile 286.211s; review cumulative 579.090s; full completion 1188.870s.
All 100,000,000 cells passed ordered replacement readback, mapping precedence,
non-cascade behavior, manifest/provenance, unchanged input digest and cleanup.
Output: 600,500,900 bytes. The terminal JSON is retained in the log.
This proves only the private CSV route against this exact isolated wheel;
no public/all-route/RC pass is claimed.

## CSV → Parquet target — PASSED

Exact candidate `15cd2d4b11ea586ca3ed48b340c5fd04ff20a55f`; wheel SHA-256
`f2bf7d5dfb90e328ada721e72acc74515b18ba565d0c07c745806e957fdc12eb`; immutable copied harness SHA-256
`cc150354883378e625e8832d1855c224e7c7dfee682577673993b17886c2188a`. Arguments: `--rows 1000000 --columns 100
--output-format parquet --max-bytes 1073741824 --max-seconds 3600`.
State `/private/tmp/apa-parquet-target-current.json`; PID 81484;
log `/private/tmp/apa-parquet-target-15cd2d4-1_i_azyj/run.log`. Full typed schema and batch readback, mapping precedence,
provenance/input digest/cleanup assertions enabled. Poll before repeating.
This is private fictional format acceptance, not public/RC clearance.

CSV → Parquet results: profile 289.725s; review cumulative 581.644s;
complete 1488.050s; output 17,398,511 bytes. All 100M cells passed ordered
readback with explicit non-null Arrow string schema, per-column mapping
precedence/non-cascade behavior, 100% replacement provenance, unchanged input
digest and cleanup. This proves the private fictional CSV → Parquet route on
the exact wheel above. 326 additional owning publication/SQL regressions passed.

The same fixture harness now supports `--output-format postgresql_sql` and
checks the complete framing, declared TEXT schema, every ordered INSERT row,
terminal COMMIT and EOF without executing SQL. 10 × 100 synthetic smoke passed
(0.193s, 24,097 bytes), Ruff passed; target SQL artifact proof remains open.

## CSV → SQL target — PASSED

Candidate `2d878f7e3353dc11b6480f2d4bddf4792d03d642`; same installed runtime wheel as 15cd2d4
(hash `f2bf7d5dfb90e328ada721e72acc74515b18ba565d0c07c745806e957fdc12eb`), harness-only subsequent commits.
Immutable copied harness SHA-256 `b7c9b3ddb5d47f03e42f45f940636a20539f795da27224bcd96c174483a9888f`.
Arguments: `--rows 1000000 --columns 100 --output-format postgresql_sql
--max-bytes 3221225472 --max-seconds 3600`. The explicit 3GiB byte ceiling
accounts for repeated column names in each SQL INSERT statement.
State `/private/tmp/apa-sql-target-current.json`; PID 82136;
log `/private/tmp/apa-sql-target-2d878f7-78goihnx/run.log`. Poll before repeating. This checks SQL text artifacts
without a database connection or execution; public/all-route/RC gates stay open.

CSV → SQL target results: profile 291.552s; review cumulative 580.806s;
complete 1435.367s. SQL artifact 2,140,502,692 bytes. All 1M ordered INSERT
statements / 100M replaced cells, schema/framing/COMMIT/EOF, provenance,
input digest and cleanup assertions passed. No SQL execution or live DB.

The local-file harness now accepts `--input-format parquet`, creating the
fictional input in 1024-row groups and explicitly configuring decoded-byte
limits. Three 2051 × 3 Parquet-input readbacks (CSV, Parquet, PostgreSQL SQL
outputs) passed, including provenance/cleanup; Ruff passed. These are small
harness checks, not Parquet-input target proof.

## Parquet → CSV target — PASSED

Candidate `b5640de2acdf0dde25da166062edd3ea7e47845b`; installed runtime wheel remains 15cd2d4
(hash `f2bf7d5dfb90e328ada721e72acc74515b18ba565d0c07c745806e957fdc12eb`); subsequent changes are harness/docs only.
Immutable harness SHA-256 `fbb61d2c1c273d64c3b7e57714b8400a4e4f4d1a1484f5fc021a318d8d8b38af`.
Arguments: `--rows 1000000 --columns 100 --input-format parquet
--output-format csv --max-bytes 1073741824 --max-seconds 3600`.
State `/private/tmp/apa-parquet-input-target-current.json`; PID 82466;
log `/private/tmp/apa-parquet-input-target-b5640de-2y7b9w4m/run.log`. Poll before repeating; no all-route/RC clearance implied.

Parquet → CSV target results: profile 320.714s; review cumulative 638.728s;
complete 1375.641s; output 600,500,900 bytes. All 100M cells passed ordered
readback, mapping precedence/non-cascade behavior, provenance, unchanged input
digest and temporary input/output cleanup. Exact candidate/runtime/harness and
budgets are retained above. No public activation or all-route claim.

## Current private fictional 1M × 100 matrix

| Input | CSV output | Parquet output | SQL artifact |
|---|---|---|---|
| CSV | PASS b49ceed | PASS 15cd2d4 | PASS 2d878f7 |
| Parquet | PASS b5640de | PASS cc3aedb | OPEN |
| PostgreSQL fictional worker | PASS 611b781 | OPEN | OPEN |
| Trino fictional result | OPEN | OPEN | OPEN |

These are installed private fixture checks, not twelve-route public/CLI/MCP
activation or live backend evidence. PostgreSQL details are in the companion
postgres-scale-acceptance.md. Final source audit and release gates remain open.

## Parquet → Parquet target — PASSED

Candidate `cc3aedb8b59aec5ff6d926066ff96120a67f9cfe`; same installed runtime wheel 15cd2d4
(hash `f2bf7d5dfb90e328ada721e72acc74515b18ba565d0c07c745806e957fdc12eb`); immutable copied harness
`fbb61d2c1c273d64c3b7e57714b8400a4e4f4d1a1484f5fc021a318d8d8b38af`. Arguments: `--rows 1000000 --columns 100
--input-format parquet --output-format parquet --max-bytes 1073741824
--max-seconds 3600`. State `/private/tmp/apa-parquet-roundtrip-current.json`;
PID 82797; log `/private/tmp/apa-parquet-roundtrip-cc3aedb-fkydavo4/run.log`. Poll before repeating.
All typed batch readback/provenance/digest/cleanup assertions enabled.
No public/all-route/RC clearance implied.

Parquet → Parquet result: profile 327.437s; review cumulative 645.564s;
complete 2169.105s; output 17,398,511 bytes. All 100M cells passed typed
ordered batch readback, column/global precedence and non-cascade checks,
100% replacement provenance, unchanged input digest and temporary cleanup.
The exact runtime wheel/harness and explicit 1GiB / 3600s limits are recorded
above. Current private fictional target matrix is 6/12; remaining targets,
public acceptance, final source audit and release gates stay open.

## Parquet → SQL target — started, result pending

Candidate `92bb1b615e75bddf5043768e96702176e1671753`; same installed runtime wheel 15cd2d4
(hash `f2bf7d5dfb90e328ada721e72acc74515b18ba565d0c07c745806e957fdc12eb`); immutable copied harness
`fbb61d2c1c273d64c3b7e57714b8400a4e4f4d1a1484f5fc021a318d8d8b38af`. Arguments: `--rows 1000000 --columns 100
--input-format parquet --output-format postgresql_sql --max-bytes 3221225472
--max-seconds 3600`. State `/private/tmp/apa-parquet-sql-target-current.json`;
PID 83384; log `/private/tmp/apa-parquet-sql-target-92bb1b6-ymaed_an/run.log`. Poll before repeating.
Complete SQL text/schema/ordered INSERT/framing/provenance/digest/cleanup
assertions enabled; no SQL execution or public/all-route/RC clearance.
