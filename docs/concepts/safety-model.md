# Safety Model

The central invariant is:

> Generated output must contain newly generated values, not copied source rows.

Source data may be read to derive bounded metadata. It is not used as a pool of
rows to shuffle, duplicate, or export.

## Trust Boundaries

Treat all of these as untrusted:

- CSV, JSON, YAML, and Parquet files;
- paths supplied to CLI or MCP tools;
- profile payloads supplied by another process;
- business-rule files and inline rule payloads;
- Trino identifiers, metadata, query results, and environment variables;
- PostgreSQL and Trino JDBC-style endpoint strings;
- output directories that may contain symlinks or existing files.

## Defenses

### Sensitive data

Likely PII and secrets are detected from both field names and values. Sensitive
columns suppress raw top values and expose masked patterns or aggregate metadata
instead. Sensitive examples use an opaque placeholder rather than intentionally
preserving source values. Non-sensitive category profiles replace source values
with ranked synthetic labels by default. An explicit field-scoped local
allowlist may preserve only a reviewed bounded non-sensitive business enum or
constant after content, cardinality, and value-length checks. Rare free text,
PII, secrets, identifiers, and quasi-identifiers are never eligible.

Approved exact values may appear only in local profiles, reviewed specs,
deterministic generated rows, and local SQL export. External providers receive
field-scoped labels, and default MCP responses, logs, and public errors remain
source-literal free.

### Source-row reuse

Generation uses a reviewed specification and a local seeded random generator.
Runtime checks reject exact source-row reuse in supported CSV workflows.
The comparison covers complete rows only and runs only when the source CSV is
available to that workflow. It does not detect every partial-value,
quasi-identifier, or statistical similarity between source and output.

### Filesystem

Input and output paths must be distinct. New bundles are assembled in a
temporary sibling directory and published only after size and validation
checks. Workspace-bound MCP paths reject traversal and symlink escapes.

### Trino

Trino access is read-only, allowlisted, bounded by client row limits and
server-side time and scan budgets. Unsafe query shapes and likely sensitive
projections are rejected before execution. The default aggregate-only tools
return only source-literal-free metadata and aggregates. The explicit opt-in
row-returning tool `run_safe_select` recursively masks every returned string in
bounded scalar or composite values and any non-string field or value recognized
as sensitive. Other non-string source values may remain, so those rows are not
source-free or anonymous.

### PostgreSQL

Direct PostgreSQL profiling uses the optional driver through a forced
read-only session. Schema, table, and column allowlists are mandatory, and one
shared statement/result/deadline budget bounds metadata and aggregate queries.
The profiler accepts no caller SQL and reads no source rows. Qualified local
category selectors may retain only values that pass the selective local policy
above.

PostgreSQL `schema.table.*` and Trino `catalog.schema.table.*` column selectors
are authorization syntax, not SQL. They are expanded from bounded metadata for
one exact allowed table into a deterministic explicit-column snapshot before
aggregates run. They do not authorize source rows, local exact values, category
literals, caller projection stars, providers, default MCP literals, logs, or
errors.

PostgreSQL and Trino may accept credential-free JDBC-style endpoint syntax.
Parsing happens before client construction and rejects userinfo, secrets,
session-changing or unknown properties, malformed escapes, ambiguous paths,
and conflicting component configuration. The complete URL is discarded after
normalization and is never written to profiles, manifests, MCP responses,
provider payloads, logs, or public errors.

### Resource limits

The project limits input bytes, rows, columns, cells, YAML complexity, Parquet
expansion, generated rows, output bytes, available disk reserve, rule work,
query work, and wall-clock generation time.

## What The Project Guarantees

For supported workflows and accepted inputs, the project is designed to:

- avoid copying complete source rows;
- avoid writing raw detected PII into safe profiles;
- regenerate identifiers and sensitive semantic values;
- produce logically deterministic output for the same spec, rules, seed,
  locale, runtime, dependencies, serializer, and generator version;
- validate schema, relationships, constraints, and business rules;
- record provenance and safety flags in a generation manifest.

The manifest records those effective inputs plus SHA-256 evidence for generated
artifacts. Byte-for-byte identity is expected only when the complete recorded
environment is unchanged. It is not guaranteed across Python, dependency,
serializer, operating-system, or package versions, even when logical values and
validation results remain equivalent.

## What It Does Not Guarantee

The project cannot decide whether every ambiguous business field is sensitive.
It also cannot prove that an inferred distribution is legally or statistically
safe for every use case. The project does not currently implement differential
privacy, k-anonymity, l-diversity, or a privacy budget, and makes no statistical
privacy guarantee. Treat generated data as requiring a domain-specific privacy
review before distribution.

Human review is still required for:

- domain-specific identifiers and rare free text;
- inferred relationships and constraints;
- privacy requirements outside the built-in detectors;
- organization-specific retention and access controls;
- downstream systems that may log or redistribute generated data.

Do not send production data, raw PII, credentials, or tokens to an LLM while
reviewing profiles or specifications.

## Acceptance Checklist

Before publishing a generated dataset:

- manifest says `synthetic: true`;
- manifest says `source_rows_copied: false`;
- deterministic validation passed;
- business validation passed when rules were used;
- seed, row counts, format, and fingerprints are correct;
- profile and generated samples contain no unexpected sensitive values;
- the output is stored outside the source path.

See [Review The Output](../getting-started/review-output.md) for the practical
review sequence.
