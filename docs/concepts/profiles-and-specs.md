# Profiles And Specs

Profiles and specifications have different roles.

## Safe Profile

A profile describes source structure without becoming a copy of the source
dataset. It can contain:

- field names and inferred types;
- null ratios and approximate distinct counts;
- numeric ranges and percentiles;
- date and timestamp ranges;
- safe distributions for non-sensitive low-cardinality fields;
- string length statistics and masked sensitive patterns;
- inferred relationship and constraint candidates.

A profile must not contain source rows, raw PII, credentials, tokens, or rare
free-text values. Exact values are disabled by default. An explicit
field-scoped local allowlist may retain a reviewed bounded non-sensitive
business enum or constant after content, cardinality, and value-length checks.

Create one from a CSV folder:

```bash
test-data-agent profile-example data/example_dataset \
  --output out/profile.json
```

For example, retain a reviewed local enum while replacing every other source
literal:

```bash
test-data-agent profile-example data/example_dataset \
  --local-category orders.status \
  --output out/profile.json
```

This authorization remains local. External advisors receive deterministic
field-scoped labels, and default MCP responses do not receive the exact enum.

### SQL Query Source

This source type is available in stable `1.3.1`.

One reviewed local query file can shape a PostgreSQL or Trino virtual entity:

```bash
test-data-agent profile-query query.sql \
  --adapter postgres \
  --source-id warehouse \
  --entity paid_orders \
  --output out/profile.json
```

The initial policy accepts exactly one fully qualified, single-table `SELECT`
with explicit projections or an authorized qualified wildcard, bounded filters,
and a small deterministic scalar-expression set. It rejects joins, CTEs,
subqueries, set operations, windows, table functions, commands, volatile or
unknown functions, multiple statements, and unauthorized references before
derived aggregate work begins.

The profile records `source_fingerprint` and `source_policy_version`, not SQL
text or literals. The adapter performs a no-row schema probe followed by
bounded aggregates. Query result rows are never returned, persisted, sent to a
provider or MCP, or supplied to generation.

## DatasetSpec

`DatasetSpec` is the reviewed, executable generation contract. It contains:

- entities, fields, types, nullability, and row counts;
- primary keys and relationships;
- distributions and constraints;
- privacy annotations;
- generation settings and schema version.

Infer a spec:

```bash
test-data-agent infer-spec out/profile.json \
  --count 100 \
  --output out/dataset_spec.yaml
```

Review the spec before generation. Inferred relationships and constraints are
candidates, not unquestionable facts.

## Generation

Generation reads the specification, not source rows:

```bash
test-data-agent generate out/dataset_spec.yaml \
  --seed 12345 \
  --format csv \
  --output out/generated
```

The seed belongs to the generation request and is recorded in the effective
spec and manifest.

## Validation

```bash
test-data-agent validate out/dataset_spec.yaml out/generated \
  --output out/generated/validation_report.json
```

Validation is deterministic Python code. An AI client may plan or summarize
the workflow, but it is not the only validator.

## Versioning

The current `DatasetSpec` contract uses `schema_version: "1.0"`. Keep the
schema version, package version, `spec_sha256`,
`business_validation.rules_sha256`, and seed with any dataset that must be
reproduced later.

The complete field reference is in [DatasetSpec](../dataset_profile_and_spec.md).
