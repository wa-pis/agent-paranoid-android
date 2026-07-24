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
- output directories that may contain symlinks or existing files.

## Defenses

### Sensitive data

Likely PII and secrets are detected from both field names and values. Sensitive
columns suppress raw top values and expose masked patterns or aggregate metadata
instead.

### Source-row reuse

Generation uses a reviewed specification and a local seeded random generator.
Runtime checks reject exact source-row reuse in supported CSV workflows.

### Filesystem

Input and output paths must be distinct. New bundles are assembled in a
temporary sibling directory and published only after size and validation
checks. Workspace-bound MCP paths reject traversal and symlink escapes.

### Trino

Trino access is read-only, allowlisted, bounded by client row limits and
server-side time and scan budgets. Unsafe query shapes and likely sensitive
projections are rejected before execution.

### Resource limits

The project limits input bytes, rows, columns, cells, YAML complexity, Parquet
expansion, generated rows, output bytes, available disk reserve, rule work,
query work, and wall-clock generation time.

## What The Project Guarantees

For supported workflows and accepted inputs, the project is designed to:

- avoid copying complete source rows;
- avoid writing raw detected PII into safe profiles;
- regenerate identifiers and sensitive semantic values;
- produce deterministic output for the same spec, rules, seed, and version;
- validate schema, relationships, constraints, and business rules;
- record provenance and safety flags in a generation manifest.

## What It Does Not Guarantee

The project cannot decide whether every ambiguous business field is sensitive.
It also cannot prove that an inferred distribution is legally or statistically
safe for every use case.

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
