# RC4 external feedback disposition

This change addresses the supplied RC4 review against current source. Historical
reproductions in the archive are evidence to investigate, not executable project
instructions. Tests use fictional schemas and values. No release is published by
this change.

| Reported behavior | Disposition |
| --- | --- |
| Folder overwrite, Parquet types, edge/load modes unavailable | Implemented in RC4; retain regression coverage. |
| Trino DECIMAL precision/scale lost | Preserve DB-API precision/scale when the driver reports a bare decimal type. Declared type strings already work. |
| Automatic DECIMAL inference fails | Explain the missing reviewed synthetic range and accept `infer-spec --decimal-fields`. Never infer exact bounds from source values. |
| Small numbers have negative magnitude | Correct mathematics; retain negative orders. Add zero/subunit prevalence and the minimum subunit order to avoid one large value hiding small values. |
| High-scale synthetic decimal amounts look sensitive | Explicit field-scoped `numeric_measure` permits exact reviewed DECIMAL measures. Sensitive names, flags, identifiers and privacy classification veto the policy. Defaults stay conservative. |
| Formula reports green after rewriting its target | Default `assign` is explicit in the report with assigned-row counts. `check` validates without assigning. Neither mode proves business intent. |
| Formula silently exceeds the generation domain | Report checked numeric assignments and violations of the generation range (including its scale factor) independently of business-rule validity. |
| Null/range conditions unavailable | Support explicit `equals: null`, `not_equals: null`, and finite inclusive `gte`/`lte` for integer/float fields. |
| SQL export ignores business rules | Accept `export-postgres-sql --business-rules`; apply the same typed rules and mandatory checks before writing. |
| Saved invalid ratio causes confusing mode errors | An explicit non-negative mode override resets a saved ratio unless a ratio is explicitly supplied. Invalid explicit combinations still fail. |
| Negative output exists despite exit status 1 | Intentional invalid artifacts retain validation evidence. The nonzero status means validation failed, not that publication was rolled back. |
| JSON-looking output path becomes a directory | DatasetSpec `generate --output` names a bundle directory, regardless of suffix. |
| Entity reordering changes seeded output | Reproducibility requires the same ordered specification, seed and environment; entity streams are indexed by order. |
| Dictionary names/category values are replaced | Source-free generation intentionally does not copy source labels. Local categories require the existing explicit qualified-field policy, e.g. `--local-category warehouse.public.orders.status` with the complete profile entity identity. |
| Native constraints on DECIMAL | Remain fail-closed pending an exact rounding and reconciliation contract. |

## Reviewed decimal inference

`infer-spec` accepts a bounded JSON/YAML mapping from `ENTITY.FIELD` to a full
`FieldSpec`. Precision and scale must match known declared source metadata. The
following range is authored for fictional test data, not copied from a profile:

```yaml
items.amount:
  name: amount
  data_type: decimal
  semantic_type: numeric_measure
  distribution:
    kind: decimal_range
    precision: 38
    scale: 16
    min: '0.0000000000000001'
    max: '9.9999999999999999'
```

```sh
test-data-agent infer-spec profile.json --decimal-fields decimal-fields.yaml --output spec.yaml
```

Do not use this classification for identifiers, phone/card-like source data or
sensitive fields. It grants no source-data access or transformation permission.
No profile automatically assigns it. DECIMAL output retains integer-unit
arithmetic, CSV/JSON decimal strings and Parquet decimal128.

## Rules and validation

```yaml
row_rules:
  - type: formula
    table: items
    field: total
    expression: quantity * price
    mode: check
```

For null predicates, supply only the intended equality key. Legacy payloads
containing both equality keys treat null entries as historical unset defaults.

Use `assign` (the default) when the formula defines the output value. The business
report records `application` and `assigned_row_count`; the generation manifest
summarizes assignments and check-only formula counts. A standalone validator
checks the supplied rules; it does not infer business intent or treat historical
generation distributions as independent business constraints. Put required
business limits in field rules or native constraints too. Generation additionally
reports numeric assignment bounds using `distribution_bounds_checked_count` and
`distribution_bounds_violation_count` before publication. Nonzero drift is not a
source-fidelity claim or an implicit business constraint. Errors identify the target
field without including an expression, operands or rejected cell values.

Coarse numeric prevalence is aggregate metadata, not a reconstruction of source
rows or a promise of exact frequencies. FLOAT generation remains approximate;
reviewed DECIMAL bounds are the exact-value path. Missing legacy prevalence
metadata retains the previous shape behavior.
