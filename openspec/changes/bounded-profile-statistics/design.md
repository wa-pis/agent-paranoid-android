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
