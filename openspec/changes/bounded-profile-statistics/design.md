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
