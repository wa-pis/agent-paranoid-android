# Review The Output

A successful command is not the end of the review. Use the artifacts in the
bundle to decide whether the synthetic dataset is safe and useful.

## Review Order

1. Read `generation_manifest.json`.
2. Read `validation_report.json`.
3. Read `business_validation_report.json` when business rules were supplied.
4. Review the effective `dataset_spec.yaml` or `dataset_spec.json`.
5. Inspect a small sample of generated rows.

## Manifest Checks

Require all of these conditions:

```json
{
  "synthetic": true,
  "source_rows_copied": false,
  "validation_valid": true
}
```

Also confirm:

- `seed` is the value requested by the caller;
- `row_counts` match the requested scale;
- `output_format` is correct;
- `package_version` and `dataset_spec_schema_version` are recorded;
- `spec_sha256` is present;
- `business_validation.rules_sha256` and its summary are present when rules
  were used.

## Validation Report

`validation_report.json` reports deterministic checks for:

- entity and field schema;
- primary-key uniqueness;
- relationships and foreign keys;
- field and row constraints;
- temporal and formula constraints;
- aggregate reconciliation.

Do not treat a missing report as success. A failed report should block
publication of the generated dataset.

## Profile Review

Profiles should contain metadata such as types, null ratios, ranges,
percentiles, approximate distinct counts, safe low-cardinality distributions,
and masked patterns.

Stop and investigate if a profile contains:

- a real email address, phone number, token, credential, or private key;
- a source row copied as a nested object or list;
- rare free-text values that could identify a person;
- an unexpected identifier distribution.

## Generated-Row Review

Inspect generated data for domain usefulness, but do not compare or publish raw
source rows during that review. For sensitive domains, perform review in the
same protected environment as the source data.

Re-run with the same spec, rules, package version, and seed when reproducibility
is required. A change to any of those inputs can legitimately change output.

See [Safety Model](../concepts/safety-model.md) for guarantees and limitations.
