# Source-Independent Profiling Verification

Implemented and locally verified, unreleased, 2026-11-22.

## Coverage

| Source route | Applied policy and checked boundary |
| --- | --- |
| CSV file / snapshot / row digests | Shared semantic evidence; complete exact counts with set-to-DuckDB handoff; same iterator, full-profile and row-digest parity |
| CSV folder | Shared semantic and name risk; existing exact backend, private keyed spill and deadline/cleanup checks retained |
| Parquet | Native Arrow physical types, dictionary value types and conservative name risk; all four entry points forbid column-row reads |
| PostgreSQL table | Existing exact count evidence forwarded; native numeric category risk checked before profile publication |
| Trino table | Shared weighted source evidence and native numeric-summary protection; existing query counts and bounds retained |
| PostgreSQL / Trino query | Sensitivity follows aliases, expressions and wildcard expansion; unsafe local categories rejected before their value query |
| Legacy JSON profiles | Shared source-scalar normalization and summary suppression across every tested source label |
| Typed JSON profiles / specs | Shared safety rejects sensitive numeric categories and source summaries; explicit reviewed metadata and spec numeric scaling keep their contracts |

Source-label tests include CSV, folder, Parquet, PostgreSQL, Trino, both query
labels, JSON/legacy and an arbitrary custom label. `AGENTS.md` now requires this
coverage for shared policy changes.

Available evidence still differs: schema-only Parquet and aggregate-only
database routes do not claim complete content recognition. No new source-row
reads, query families, SQL privileges, optional dependencies or automatic
streaming modes were introduced. All normalized specifications use the shared
generation/validation policy; existing explicit streaming eligibility and
CLI/MCP/review boundaries remain intact.

## Safety And Determinism Evidence

- **93 source-profile cases** cover source-neutral suppression, safe shapes,
  discriminator integrity, lower-bound cardinality and historical CSV evidence.
- **57 name cases** cover shared words/phrases, aliases, conflicting hints,
  old positives, JSON planning and metadata-only Parquet.
- **92 numeric-source cases** cover native int/float/Decimal, local categories,
  weighted context, typed profile/spec rejection, all database routes, safe
  failures and numeric-summary suppression without extra Trino queries.
- **34 query cases** cover both dialects, aliases, expressions, wildcards,
  physical-type preservation, count forwarding and pre-query category rejection.
- **5 Parquet cases** cover all four entry points, 14 Arrow type combinations,
  forbidden row reads and deterministic seeded generation.
- **9 single-CSV cases** cover file/snapshot/digest parity, trigger-cell handling,
  exact counts beyond the old ceiling, late weak evidence, no reopen, backend
  failure, native generation-budget propagation and bounded remaining time.
- Advisor regressions preserve sanitization of every JSON scalar and numeric
  bounds in safe profiles, and reject sensitive native numeric evidence before
  building a provider request.
- Existing frozen strict detector, generated-row privacy, semantic corpus,
  private-spill, mandatory validation and atomic-export regressions passed.

Independent review also ran 24 real-DuckDB parity checks across eight handoff
thresholds and three entry points, including null/empty columns, repeated
identifiers and late strong/weak evidence. Complete profiles and row-digest sets
matched the set path. Another 6,011 synthetic string comparisons against the
pre-task CSV normalizer produced zero tag/exception-type differences. A 6,000-name
probe retained all 2,967 old positives, added 897 conservative positives and
had zero downgrades. These are synthetic regression checks, not real-world
accuracy estimates.

## Executed Checks

- Full suite: **2704 passed, 10 skipped** in **74.92 seconds**.
- Line coverage: **91.94%**, 12,365 / 13,449 statements.
- `ruff check src tests scripts`: passed.
- `mypy src/test_data_agent`: passed, 124 source files.
- Strict MkDocs build, strict OpenSpec validation, documentation regressions
  and `git diff --check`: passed.
- Independent code review: no remaining actionable findings.

Machine-readable audit counts and implementation hashes are in
[`verification.json`](verification.json). Earlier OpenSpec/benchmark evidence
was not rewritten.

## Migration And Limits

Folder cache format **9** invalidates earlier inferred name-risk metadata.
Query policy **1.1** changes new query fingerprints and preserves sensitive
projection provenance. Saved profiles and plans are not silently rewritten;
reprofile them to obtain the corrected policy. The additive CSV evidence kind
defaults old payloads to `unspecified`, and historical censored counts remain
ineligible for inferred pools.

The optional profiling extra is required when local distinct state crosses the
shared threshold. Input, row, cell, deadline, memory-buffer and spill bounds
still apply; there is no hard total-process-memory or unlimited-row claim.
Live database integrations were not run. The subsequent public CSV performance
benchmark is recorded separately in [benchmark.md](benchmark.md), including all
twelve runs, privacy/determinism checks, stage times and peak memory. All
fixtures and probes were synthetic; no production data or external AI provider
was used. No version, commit, tag, release or publication was selected.
