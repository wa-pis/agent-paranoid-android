# Installed transformation format and refusal matrix — 2026-11-10

This completes the selected registered matrix at **1,000,000 × 100** with
Agent Paranoid Android **1.7.0rc3**, from the published wheel built from
`09b6fb207b22364ff41f70d7b51abe30d1a458fa`, SHA-256
`5345e27a5a8311d72cedda193747c861f2d646ef0de374bd9bd74e1405c5195d`.
The isolated interpreter was CPython 3.15.2 on macOS arm64, with MCP SDK 2.2.0
and PyArrow 26.0.1. Each subprocess used a clean environment. The campaign
uses only fictional replacement-only inputs; no receipts are issued, no SQL
text is executed, and no live database or AI provider is contacted.

The [five earlier registered passes](registered-scale-acceptance-2026-11-09.md)
combine with the **31 new format cases** below: 12 single-source CLI, 12
single-source SDK stdio MCP, six common SDK stdio MCP and six configured
SDK stdio MCP across PostgreSQL and Trino. The earlier combined MCP timeout
remains in that report. The three isolated refusals below are new full-size
evidence, not a reinterpretation of the timed-out attempt.

Single-source SQL inputs are already captured fictional result envelopes.
Configured MCP runs exercise the actual registered tools, allowlists,
isolated capture workers and retained sessions, substituting only the closed
fictional database driver. They assert no reconnection after review and
capture removal after publication. Each batch contains a separate 2 × 2
Parquet-to-CSV control. This matrix does not separately measure batch CLI
front ends, live networks, preservation or memory/throughput guarantees.

Every successful route verified all 100,000,000 cells and their order, exact
review binding, mixed provenance, unchanged inputs and scratch cleanup.
CSV, typed Parquet and PostgreSQL SQL text were read back in full. SQL text
was compared as a file, including its schema and statements. Figures are
harness monotonic end-to-end timings under overlapping workloads.

Each case had a separate finite 3,600 s deadline and a 1 GiB byte ceiling
for ordinary output. SQL-text output used an explicit 3 GiB ceiling; for the
single-source harness this setting also applies to the input budget, while
batch input stays at 1 GiB with a 512 MiB per-file/capture bound and 1 MiB
review cap. Other settings match the earlier registered report. The output
byte counts exclude metadata and the batch control.

## Additional format cases

| Registered route | Input | Output | End-to-end (s) | Output bytes |
| --- | --- | --- | ---: | ---: |
| Single CLI | CSV | Parquet | 1835.302 | 17,398,511 |
| Single CLI | CSV | PostgreSQL SQL text | 1747.728 | 2,140,502,692 |
| Single CLI | Parquet | CSV | 1716.202 | 600,500,900 |
| Single CLI | Parquet | Parquet | 2032.464 | 17,398,511 |
| Single CLI | Parquet | PostgreSQL SQL text | 1967.590 | 2,140,502,692 |
| Single CLI | PostgreSQL result | CSV | 1729.609 | 600,500,900 |
| Single CLI | PostgreSQL result | Parquet | 1930.440 | 17,398,511 |
| Single CLI | PostgreSQL result | PostgreSQL SQL text | 1885.566 | 2,140,502,692 |
| Single CLI | Trino result | CSV | 1676.163 | 600,500,900 |
| Single CLI | Trino result | Parquet | 1877.038 | 17,398,511 |
| Single CLI | Trino result | PostgreSQL SQL text | 1856.276 | 2,140,502,692 |
| Single SDK stdio MCP | CSV | CSV | 1728.616 | 600,500,900 |
| Single SDK stdio MCP | CSV | Parquet | 1904.589 | 17,398,511 |
| Single SDK stdio MCP | CSV | PostgreSQL SQL text | 1880.477 | 2,140,502,692 |
| Single SDK stdio MCP | Parquet | CSV | 1919.872 | 600,500,900 |
| Single SDK stdio MCP | Parquet | PostgreSQL SQL text | 2086.491 | 2,140,502,692 |
| Single SDK stdio MCP | PostgreSQL result | CSV | 1818.508 | 600,500,900 |
| Single SDK stdio MCP | PostgreSQL result | Parquet | 2047.694 | 17,398,511 |
| Single SDK stdio MCP | PostgreSQL result | PostgreSQL SQL text | 1977.544 | 2,140,502,692 |
| Single SDK stdio MCP | Trino result | CSV | 1775.179 | 600,500,900 |
| Single SDK stdio MCP | Trino result | Parquet | 1968.432 | 17,398,511 |
| Single SDK stdio MCP | Trino result | PostgreSQL SQL text | 1977.611 | 2,140,502,692 |
| Common SDK stdio MCP | CSV | CSV | 2026.097 | 200,001,000 |
| Common SDK stdio MCP | CSV | Parquet | 2266.039 | 15,142,366 |
| Common SDK stdio MCP | CSV | PostgreSQL SQL text | 2260.865 | 1,840,002,792 |
| Common SDK stdio MCP | Parquet | Parquet | 2404.439 | 15,142,366 |
| Common SDK stdio MCP | Parquet | PostgreSQL SQL text | 2496.070 | 1,840,002,792 |
| Configured PostgreSQL SDK stdio | PostgreSQL result | Parquet | 1998.370 | 15,142,366 |
| Configured PostgreSQL SDK stdio | PostgreSQL result | PostgreSQL SQL text | 1933.318 | 1,840,002,792 |
| Configured Trino SDK stdio | Trino result | Parquet | 1944.284 | 15,142,366 |
| Configured Trino SDK stdio | Trino result | PostgreSQL SQL text | 1907.868 | 1,840,002,792 |

## Isolated SDK stdio refusals

All three calls used the same reviewed fictional 1,000,000 × 100 CSV
fixture and separate workspaces. Each observed a sanitized rejection with
zero output bytes, unchanged inputs and workspace inventory, and cleanup.
The overwrite test also verified the exact pre-existing owner artifact.

| Refusal | End-to-end (s) |
| --- | ---: |
| Wrong snapshot digest | 1123.115 |
| One-byte output cap | 1351.469 |
| Existing destination | 1662.271 |

## Reproduction

Use installed Python with `-I`, `--rows 1000000 --columns 100`, and the
published wheel above. For single-source positive cases, run
`scripts/accept_transformation_csv_scale.py` with the recorded entrance and
formats, `--max-seconds 3600 --execution-only`, and
`--max-bytes 1073741824` (SQL text: `3221225472`). For a refusal, use
`--entrance mcp --refusal digest|budget|overwrite` in place of
`--execution-only`. For batches, run
`scripts/accept_transformation_batch_scale.py common|postgres|trino`,
choose `--output-format`, and select `--input-format` only for common.

Measured harness identities:
- `1ef9ef2cba3a19559d55e44983fd5d58b51ac9b0087cef04cd54747cf470a9be` — ten file cases; earlier installed scale harness.
- `253583b91f6a7103056b3fe52374fee10be15042853cda9933ba1de29121968e` — twelve saved-result cases and three refusals.
- `0c4b7aae136eb79a8e149b20a138e7d6989e3efeb683c9a838b4f432b00156ed` — nine common/configured cases.
