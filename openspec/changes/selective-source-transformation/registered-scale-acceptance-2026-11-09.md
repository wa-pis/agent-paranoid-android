# Installed registered transformation capacity — 2026-11-09

Runtime: published Agent Paranoid Android 1.7.0rc3, source
`09b6fb207b22364ff41f70d7b51abe30d1a458fa`, public wheel SHA-256
`5345e27a5a8311d72cedda193747c861f2d646ef0de374bd9bd74e1405c5195d`.
The existing isolated environment imports from installed site-packages only:
CPython 3.15.2, macOS arm64, MCP SDK 2.2.0, PyArrow 26.0.1. Child processes
use a clean environment without provider credentials or deployment access.

## Test scope

- Two single-source installed public routes: registered CLI CSV → CSV and
  genuine SDK stdio MCP Parquet → Parquet. Existing scale harness SHA-256
  `08510430c19469869b013fd96c8cfb3e758c76540e7db023c5c235bfa614009c`.
- Three installed saved-profile routes: public common MCP Parquet → CSV;
  configured PostgreSQL → CSV; configured Trino → CSV. All three use the
  registered tools over real SDK stdio, each with one target-size input and a
  separate two-row, two-column Parquet control. Only the configured driver
  factory is replaced for the SQL routes; real reference parsing, deployment
  allowlists, isolated capture workers, session admission/expiry, exact review,
  batch validation and publication are used. No sockets or live DBs.
- 1 GiB total-input/output and decoded-Parquet ceilings, explicit finite
  3600-second allowances. The common/configured harness additionally sets
  512 MiB per-file/capture and 1 MiB review; configured admission reserves
  1 GiB for one active session with a non-renewable 3600-second lifetime.
  Trino uses its own finite worker invocation budget (3600 s); the PostgreSQL
  adapter retains its 120 s default beneath the session deadline. These are
  fixture settings, with no product default changes.

The executable procedures are `scripts/accept_transformation_csv_scale.py`
and `scripts/accept_transformation_batch_scale.py` (commit
`e1caa18f9c833c01b787f54825a70102f6446bd9`, SHA-256
`90a010688ad5013943eae504396f8c5d59a7047407bf5a9e54c93594e6f7b47a` for
common and PostgreSQL; Trino adds its own deadline in
`2bef6a39dab983f47d25f04aab62d2771c4cfbb0`, SHA-256
`7dd481f6ec823c5f8f21f6a412404097f307da2758130a2a8406334479f0e139`).
Use the installed Python
with `-I`. Public CLI uses `--rows 1000000 --columns 100 --max-bytes 1073741824
--max-seconds 3600 --entrance cli`; public MCP uses the same budgets and shape,
`--input-format parquet --output-format parquet --entrance mcp`. The batch
script takes `common`, `postgres`, or `trino` as its route argument. Small
batch smokes at 2,051 × 100 completed for all three routes before target runs.

This acceptance measures replacement-only fictional data, not a generation
throughput SLA. No preservation receipt, human acceptance, live database,
external provider or new activation authority is involved.

## Results at 1,000,000 × 100

All five registered route selections completed on November 9–10 (Samara time).

Each completed route checks all 100,000,000 cells and the exact row order,
mixed-origin provenance, unchanged inputs and scratch cleanup. Configured runs
also check that the isolated capture is removed and no connection is opened
between review and completed publication. The CLI also passed all three
target-size refusals; the successful MCP replay checks publication separately.
The output byte count is for the
target data file, excluding manifests and the tiny batch control.

| Installed route | Review checkpoint (s) | End-to-end (s) | Output bytes |
| --- | ---: | ---: | ---: |
| Registered CLI CSV → CSV | 528.240 | 3355.787 | 600,500,900 |
| Registered MCP SDK stdio Parquet → Parquet (publication replay) | 552.489 | 2052.353 | 17,398,511 |
| Common MCP SDK stdio Parquet → CSV | 882.777 | 2361.507 | 200,001,000 |
| Configured PostgreSQL SDK stdio → CSV | 934.987 | 1823.197 | 200,001,000 |
| Configured Trino SDK stdio → CSV | 922.317 | 1847.678 | 200,001,000 |

Elapsed values are each harness's monotonic measurements. Runs overlapped and
the host briefly suspended, so these times are not a calibrated performance
benchmark. The five route selections exercise the distinct registered entry
points; they do not repeat every output-format combination in the historical
12-route private matrix or measure external database/network performance.

### Public MCP timeout and isolated publication replay

The first Parquet → Parquet SDK stdio run used the default combined scenario
with all refusal cases. Profiling completed at 285.696 s and local review at
571.563 s. The harness's outer 3600-second client deadline raised
`TimeoutError` before a complete result was recorded. Scratch inputs and
outputs were removed. This is a failed timed campaign, not evidence of a
product request deadline or a target-size refusal pass.

The follow-up adds only `--execution-only` (commit
`53fbd2693003cb20f2d6052e428d2a4605ec6d7a`, harness SHA-256
`1ef9ef2cba3a19559d55e44983fd5d58b51ac9b0087cef04cd54747cf470a9be`) to the
same public MCP command. It keeps the exact public review digest, bounded
execution, full typed output readback, provenance and cleanup, and makes no
target-size refusal claim. Its 2,051 × 100 smoke passed in 5.249 s.
The million-row replay passed in 2052.353 s, with complete typed readback
and cleanup. The earlier small registered MCP scenarios remain the refusal
evidence; this successful run makes no claim about the combined hour-long run.
