# Design

Retain max_abs_magnitude = floor(log10(max(abs(nonzero values)))) and its negative
range. Truncation changes 0.04 from exponent -2 to -1; excluding subunit values
makes an all-subunit column unknown. Neither is an acceptable correction.

Reuse existing `profiling/numeric_shape.py`, `NumericShapeDistribution` and seeded
sampling. Verify non-null denominators, empty/all-zero behavior, bounded ratios
and missing-statistic semantics. Cover PostgreSQL table/query, Trino query and
sensitive numeric MCP aggregates, including existing DECIMAL summary dispatch.
Keep exact decimal generation bounds
reviewer-supplied. Do not generate more precise evidence than the profile supports.

For Parquet, use bounded reads and explicit uncertainty rather than metadata-only
fabricated counts. Temporal extrema do not establish monthly granularity: any
discrete-period model needs bounded evidence and privacy controls of its own.

Measure query counts for narrow and wide fictional schemas. Batch aggregates only
within SQL-size, column, result-cell, deadline and scan limits. No temporary table
or other write is permitted. Category preflight can reject names/scopes before
access; actual cardinality still requires bounded aggregate evidence.


Parquet S5: reuse the existing scalar inspection rather than opening a second
reader. Count a bounded private set of SHA-256 encodings of Arrow-native scalar
values, normalize signed floating zero, and expose only the non-null distinct
ratio plus existing exact/lower_bound kind. At 10,000 retained digests, an unseen
value marks overflow; repetitions at the cap remain exact. Binary/composite and
nonfinite numeric equality remain unknown. The metadata null policy stays
independent. No primary-key nomination or identifier pool is added by this
change. Full row-count consistency is checked before publishing evidence.


## Temporal bounds and granularity (S6)

A fictional interval from year 1000 to year 3000 with an upper fraction of
.999999 independently reproduces a one-microsecond overshoot. Converting its
`timedelta.total_seconds()` float to int rounds the allowed maximum up. Compute
whole seconds from integer days and seconds instead. This keeps existing
second-resolution sampling, lower microseconds, offset handling and missing-bound
fallbacks; it does not establish the cause of the external report's date.

Min/max dates do not establish a calendar grain. A bounded future month-start
route must separate candidate evidence from reviewed generation configuration:

- Evidence is metadata only: inspected non-null count and counts satisfying an
  explicit calendar predicate, with unknown on missing/incomplete evidence.
  A min/max interval alone never yields a month-start declaration. Empty input
  is unknown; partial coverage is a candidate, not a fidelity claim.
- Local profiling reuses its existing bounded scan. SQL uses trusted aggregate
  predicates only, charged to existing result-cell, query, deadline and scan
  budgets; no raw date projections or source-value lists are introduced.
- The first reviewed calendar model should support DATE month starts, with
  explicit inclusive bounds, rather than conflate timestamp timezone/calendar
  semantics. Select uniformly among eligible first-of-month dates. An interval
  with no eligible date rejects before generation or publication.
- Unknown grain preserves current day/second range generation. A reviewed grain
  must be typed, fingerprint-bound and separately checked in validation and all
  output formats. Source frequencies are not reproduced. Old profiles and plans
  do not acquire a grain automatically; approval must be renewed after changes.
- Runtime/calendar schema changes, provider summaries and candidate release
  acceptance need their own implementation tests before activation. The current
  bounds correction activates no new inferred calendar behavior.


A second independent reproduction supplies only maximum 2010-01-01. The default
minimum 2020-01-01 exceeds it, and the previous zero-clamping returned 2020
outside the supplied maximum. Reject reversed effective intervals before row
publication, with a fixed hint to supply ordered explicit endpoints. The same
check rejects a supplied minimum beyond the default maximum; endpoint defaults
and valid intervals are unchanged. Do not silently clamp contradictory intervals.
