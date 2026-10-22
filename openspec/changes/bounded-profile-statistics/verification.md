# Numeric prevalence verification

The RC4 regression verifies mixed-scale sampling, zero-only generation and
negative subunit orders. New fictional boundary tests verify non-null count
denominators, legacy omitted metadata/serialization and rejection of Boolean,
negative, fractional, missing or excessive counts and inconsistent subunit orders.
No additional source query or duplicate metadata field is introduced.

PostgreSQL, Trino and SQL-query summary builders already share `prevalence_sql`.
Producer/provenance coverage, unavailable external profile versions, Parquet
distinct evidence, temporal granularity and query-cost batching remain open.
Existing prevalence is not a claim of exact decimal bounds or source fidelity.
