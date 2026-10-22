# CSV Profiling Details

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
| Parquet | Distinctness is currently unknown, even with row-group statistics. No pool or primary key is inferred from it. Missing null statistics also block automatic spec inference. |

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
Folder cache format 7 recomputes older cached profiles. Reprofile saved standalone
artifacts and review the new specification rather than trusting old nonfinite
extrema; existing approved plans are not silently rewritten.

Generated string identifiers use the `synthetic_` prefix. This changes exact
seeded identifier output relative to earlier releases, without changing the
profile or specification schema version.
Short string patterns reserve random suffix space instead of filling the entire
requested length with a prefix.
