# Source-Independent Profiling

## Status

Implemented and locally verified, unreleased, 2026-11-22. Source-matrix,
privacy, deterministic behavior and backend-equivalence regressions passed;
see [verification](validation.md). This change selects no release version,
tag or publication.

## Why

Safety and inference corrections must reach every supported source adapter.
Previously a source label could alter sensitive numeric-summary suppression;
typed numeric categories could avoid string-oriented content checks; SQL aliases
could lose the sensitivity of their physical inputs. Single-file CSV distinct
tracking also retained a ceiling that the folder path had already removed.

Equivalent policy does not mean equivalent evidence. Parquet currently supplies
schema metadata, while database sources supply bounded aggregates. Neither
should fetch source rows merely to imitate complete CSV content profiling.

## What Changes

- Enforce profile safety and sensitive-summary suppression independently of
  `source_type`, including legacy and typed JSON inputs and custom labels.
- Share bounded source-scalar privacy checks for canonical numeric evidence,
  categories and available numeric extrema, while keeping strict generated-row
  classification and explicit reviewed specification behavior separate.
- Extend conservative name sensitivity with complete words and key phrases,
  preserving every earlier positive name classification.
- Carry exact aggregate counts and SQL projection sensitivity through aliases
  and expressions; block unsafe local-category requests before their value
  query. Query-source policy becomes `1.1`.
- Keep Parquet metadata-only and interpret Arrow physical types with native
  type predicates, without reading row groups or inferring content from names.
- Give file, byte-snapshot and row-digest CSV entry points the folder path's
  exact set-to-DuckDB distinct strategy, sharing the 1,000,000-fingerprint
  handoff threshold and private keyed scratch policy without a uniqueness cap.
- Add single-CSV `unique_ratio_kind` metadata, defaulting old payloads to
  `unspecified` and marking complete new counts `exact`. Preserve historical
  censored metadata and prohibit lower-bound counts from creating pools or
  primary-key candidates. Refresh folder caches with format 9.
- Keep generation, validation and eligible explicit streaming APIs independent
  of profile origin; retain existing CLI/MCP/review opt-in boundaries.

## Safety And Compatibility

Unknown semantics never permit disclosure. Source-scalar normalization is a
profiling/input policy and does not relax raw generated-row string checks.
Reviewed `DatasetSpec` numeric scaling remains supported under its existing
safety contract. No new database row access, SQL language surface, source
backend, dependency, automatic streaming mode or approval bypass is introduced.

Saved profiles and plans are not silently rewritten. Reprofile to obtain new
inference; query policy `1.1` changes newly computed query fingerprints. Earlier
OpenSpec reports and benchmark evidence remain immutable.
