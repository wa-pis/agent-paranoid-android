# RC4 external feedback disposition

This change addresses the supplied RC4 review against current source. Historical
reproductions in the archive are evidence to investigate, not executable project
instructions. Tests use fictional schemas and values. These corrections are
assigned to the requested `1.6.0rc5`; publication remains subject to the
[release process](release.md) and [RC5 release status](rc5-release-status.md).

| Reported behavior | Disposition |
| --- | --- |
| Folder overwrite, Parquet types, edge/load modes unavailable | Implemented in RC4; retain regression coverage. |
| Trino DECIMAL precision/scale lost | Preserve DB-API precision/scale when the driver reports a bare decimal type. Declared type strings already work. |
| Automatic DECIMAL inference fails | Explain the missing reviewed synthetic range and accept `infer-spec --decimal-fields`. Never infer exact bounds from source values. |
| Small numbers have negative magnitude | Correct mathematics; retain negative orders. Add zero/subunit prevalence and the minimum subunit order to avoid one large value hiding small values. |
| High-scale synthetic decimal amounts look sensitive | Explicit field-scoped `numeric_measure` permits exact reviewed DECIMAL measures. Sensitive names, flags, identifiers and privacy classification veto the policy. Defaults stay conservative. |
| Formula reports green after rewriting its target | Default `assign` is explicit in the report with assigned-row counts. `check` validates without assigning. Neither mode proves business intent. |
| Formula silently exceeds the generation domain | Report checked numeric assignments and violations of the generation range (including its scale factor) independently of business-rule validity. |
| Null/range conditions unavailable | Support explicit `equals: null`, `not_equals: null`, and finite inclusive `gte`/`lte` for integer/float/decimal fields. |
| SQL export ignores business rules | Accept `export-postgres-sql --business-rules`; apply the same typed rules and mandatory checks before writing. |
| Saved invalid ratio causes confusing mode errors | An explicit non-negative mode override resets a saved ratio unless a ratio is explicitly supplied. Invalid explicit combinations still fail. |
| Negative output exists despite exit status 1 | Intentional invalid artifacts retain validation evidence. The nonzero status means validation failed, not that publication was rolled back. |
| JSON-looking output path becomes a directory | DatasetSpec `generate --output` names a bundle directory, regardless of suffix. |
| Entity reordering changes seeded output | Reproducibility requires the same ordered specification, seed and environment; entity streams are indexed by order. |
| Dictionary names/category values are replaced | Source-free generation intentionally does not copy source labels. Local categories require the existing explicit qualified-field policy, e.g. `--local-category warehouse.public.orders.status` with the complete profile entity identity. |
| Native constraints on DECIMAL | Supported with bounded exact arithmetic and a declared target-scale rounding contract. |

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

## Business rules across interfaces

`DatasetSpec.business_rules` carries the reviewed rules with the specification.
Python generation, CLI, MCP and approved agent workspaces use the same engine.
CSV, JSON, Parquet and PostgreSQL SQL output retain the same rule semantics;
validation and export check existing rows without reassigning formula targets.
`infer-spec --business-rules rules.yaml` embeds rules, and `validate
--business-rules rules.yaml` checks an existing dataset without modifying it.
Generation from examples also accepts `--business-rules`. Supply either embedded
rules or an external rule file/payload; competing rule sources are rejected.

For example, a specification can contain:

```yaml
business_rules:
  row_rules:
    - type: formula
      table: items
      field: total
      expression: base_amount * 0.5
      mode: assign
```

DECIMAL formulas use bounded rational arithmetic and round once using
`ROUND_HALF_UP` to the target's declared scale. Precision overflow and violations
of explicit decimal bounds fail validation. Aggregate-only business checks compare
exact totals and expressions without assigning rows or imposing a single-row
precision limit on their sum. Native aggregate mappings (`sum`,
`avg`, `count`) use the same target rounding. FLOAT operands keep their existing
finite decimal text representation; this does not recover precision already
lost in a FLOAT input. DECIMAL formula and aggregate comparisons default to zero
tolerance; an explicitly supplied `tolerance` overrides this and survives saving
and reloading. Quote exact bounds and aggregate expected values to avoid YAML
FLOAT conversion. Conditions and allowed values compare DECIMAL values exactly.

Business checks remain mandatory when optional report sections are disabled.
With reviewed business rules, mixed/negative modes construct a valid formula
baseline and then inject the planned rule violations, preserving expected-failure
accounting across embedded and external rules. They produce intentional invalid artifacts with evidence;
standalone validation reports those violations and CLI generation returns a
nonzero status when the combined validation fails. All modes retain privacy and
resource limits. Ordinary synthetic rules confer no transformation authority.
