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
free-text values.

Create one from a CSV folder:

```bash
test-data-agent profile-example data/example_dataset \
  --output out/profile.json
```

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
