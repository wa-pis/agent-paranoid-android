# CSV Profiling Details

English · [Русский](../ru/reference/profiling.md)

For the complete task, follow [First CSV Dataset](../getting-started/first-csv.md).
For profile fields, use [Profiles And Specs](../concepts/profiles-and-specs.md).
These details describe bounded evidence and do not authorize source-value reuse.

CSV opt-in preservation currently accepts string enums with at most 20 values,
each at most 64 characters, after the same content checks used for other local
category sources. Repeated low-cardinality string ID columns can remain
categorical and use synthetic category labels. Fields classified as identifiers
use a fixed synthetic key pool when a bounded repeated distinct count is
available: only the count is carried forward, not source keys or their
frequencies. Generated string identifiers use `synthetic_` plus an ASCII integer.
Censored distinct counts do not infer a pool; source identifiers are not preserved.

Repeated-key pool evidence differs by source:

| Source | Pool evidence and limits |
| --- | --- |
| Single CSV / CSV folder | A complete bounded distinct count can supply a pool; censored or overflow counts cannot. |
| PostgreSQL table / PostgreSQL or Trino query profile | Aggregate distinct counts can supply a pool for a repeated identifier. A declared PostgreSQL primary key uses fresh unique identifiers instead. |
| Trino aggregate / legacy JSON profile | A supplied positive repeated distinct count can size the synthetic pool; approximate input remains approximate evidence about the source. |
| Parquet | One bounded scalar scan reports exact or lower-bound non-null distinctness; binary, composite and nonfinite numeric evidence stays unknown. No pool or primary key is inferred from it. Missing null statistics also block automatic spec inference. |

A pool fixes the available synthetic domain, not the original key frequencies
or source row mappings. Smaller output counts and nulls can leave pool members
unused. Independent identifier domains remain separate; reviewed foreign keys
bind generated child values to generated parent keys.

Distinct counting retains at most 100,000 SHA-256 fingerprints per column,
separately from the bounded raw frequency sample. Below that limit it detects
duplicates even beyond 1,000 categories. At the limit it reports a conservative
lower bound and does not certify a primary key. Review inferred keys for larger
files. Fingerprints are internal and are not written to the profile.

Negative decimal amounts with a nonzero fractional part do not acquire phone
semantics solely from punctuation. Positive phone-shaped decimals and integral
decimal/exponent identifiers remain potentially sensitive, regardless of an
amount-like column name. Explicit sensitive names and secrets retain protection;
sensitive profiles omit ranges as well as source categories. Ambiguous financial
columns require review; local category permission is not declassification.

NaN, infinity and overflowing exponent text are not finite numeric evidence.
A column containing them is not inferred as a complete numeric distribution.
Folder cache format 8 recomputes older cached profiles. Reprofile saved standalone
artifacts and review the new specification rather than trusting old nonfinite
extrema; existing approved plans are not silently rewritten.

Generated string identifiers use the `synthetic_` prefix. This changes exact
seeded identifier output relative to earlier releases, without changing the
profile or specification schema version.
Short string patterns reserve random suffix space instead of filling the entire
requested length with a prefix.


Parquet reuses its sensitivity inspection for distinct counting: at most 10,000
private SHA-256 scalar digests per column, with the existing cell, expanded-byte
and local deadline limits. The denominator is inspected non-null rows. A new
distinct value beyond the cap changes `unique_ratio_kind` to `lower_bound`;
repetitions at the cap do not. Unsupported equality remains unknown. Null ratios
still require complete valid row-group statistics. Digests never leave the
profiler. Reprofile older Parquet artifacts and review changed fingerprints;
existing approved plans are not updated automatically.


## Local category limit recovery

`--local-category ENTITY.FIELD` preserves only explicitly authorized, bounded,
non-sensitive enums. The default source-preservation limit is 20 distinct values
of at most 64 characters; names, content and identifier protections still apply.
If a field exceeds that limit, omit its `--local-category` option and reprofile
with synthetic labels, or author an independent synthetic enum in the reviewed
DatasetSpec. Do not truncate a real enum or raise a global budget to force it
through. DatasetSpec `privacy_settings.max_safe_categories` is not permission to
increase source-profiling preservation.

Category validation stops at the first item beyond its configured ceiling.
Limits must be positive integers. SQL query profiles validate category scope,
lineage and output types after no-row schema inspection, before row-count and
column aggregates. Exact PostgreSQL scopes preflight before connection;
wildcards first require bounded metadata expansion. Invalid inputs publish no
partial trusted profile.

## Reviewed CSV numeric replacements

Positive numeric text can resemble a phone. Profiling keeps that classification,
masked patterns and sensitivity. When every non-null value parses as finite
numeric storage, ambiguous phone-like CSV columns additionally carry
`numeric_storage_type: integer|float`. This metadata contains no source values,
extrema or decimal precision; it does not establish that a field is a measure.
A late nonnumeric value, nonfinite value, formatted phone or recognized secret
cannot supply this complete numeric evidence. No majority threshold is used.

For a genuine measure, provide an independently authored synthetic range using
`infer-spec profile.json --decimal-fields reviewed.json --output dataset_spec.yaml`.
The JSON/YAML mapping uses the exact `ENTITY.FIELD` and a complete FieldSpec:

```json
{"events.quantity": {"name": "quantity", "data_type": "decimal",
  "semantic_type": "numeric_measure", "distribution": {
    "kind": "decimal_range", "precision": 8, "scale": 3,
    "min": "1.001", "max": "2.002"}}}
```

These are fictional generation bounds, not inferred source bounds. Protected
names, identifiers, primary-key candidates and relationship endpoints reject
this replacement. Fields explicitly marked sensitive for another reason also reject. Native CSV numeric
fields can use the same authored range. Declared SQL/Parquet DECIMAL retains its
existing precision/scale contract. Review the resulting spec before generation.
The source profile remains sensitive; the advisor cannot automatically clear
its classification. For an awaiting-approval agent workspace, infer to a separate file, copy only
the reviewed field into `dataset_spec.yaml`, preserve the planned generation
settings, run `agent-review`, and approve the newly reported fingerprint.
Do not overwrite the workspace spec with default inference settings.

Folder cache format 8 recomputes older profiles. An old ambiguous profile without
storage evidence requires fresh profiling; saved profiles/plans are not silently
upgraded. Evidence changes the profile fingerprint, and edited synthetic bounds
change the spec fingerprint. Obtain new review/approval after either change.
Absent evidence is omitted from serialization so unaffected legacy fingerprints
remain stable. DatasetSpec stays at schema version 1.1: no new spec field or flag.
