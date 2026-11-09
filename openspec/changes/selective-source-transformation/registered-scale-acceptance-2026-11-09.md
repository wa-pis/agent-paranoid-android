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
  These are fixture settings, with no product default changes.

The executable procedures are `scripts/accept_transformation_csv_scale.py`
and `scripts/accept_transformation_batch_scale.py` (commit
`e1caa18f9c833c01b787f54825a70102f6446bd9`, SHA-256
`90a010688ad5013943eae504396f8c5d59a7047407bf5a9e54c93594e6f7b47a`). Use the installed Python
with `-I`. Public CLI uses `--rows 1000000 --columns 100 --max-bytes 1073741824
--max-seconds 3600 --entrance cli`; public MCP uses the same budgets and shape,
`--input-format parquet --output-format parquet --entrance mcp`. The batch
script takes `common`, `postgres`, or `trino` as its route argument. Small
batch smokes at 2,051 × 100 completed for all three routes before target runs.

This acceptance measures replacement-only fictional data, not a generation
throughput SLA. No preservation receipt, human acceptance, live database,
external provider or new activation authority is involved.
