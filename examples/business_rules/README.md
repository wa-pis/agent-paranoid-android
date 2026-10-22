# Complete business-rules format

Start with [rules.yaml](rules.yaml): a commented, runnable example of every
current rule family and every model option. Its source-free companion
[dataset_spec.yaml](dataset_spec.yaml) defines four fictional customers and
24 orders. The small introductory example remains
[orders_rules.yaml](../orders_rules.yaml).

The standalone [JSON Schema](../../schemas/business_rules.schema.json) is
exported from the same `BusinessRules` model used at runtime. The first YAML
comment associates it with editors that support YAML language-server schemas.
JSON uses the same object/arrays/keys; comments are YAML-only. Schema validation
checks structure; Python additionally checks predicates, formulas, references,
types, privacy and budgets against the effective DatasetSpec.

## Run the whole example

From the repository root, review the two input files, then run:

```bash
test-data-agent generate examples/business_rules/dataset_spec.yaml \
  --business-rules examples/business_rules/rules.yaml \
  --seed 12345 --format json --output out/business-rules
```

Use a fresh output destination. The bundle contains generated entity files,
`dataset_spec.yaml`, `generation_manifest.json`, `validation_report.json` and
`business_validation_report.json`. This example has `valid: true` and zero
business-rule failures in valid mode. Its fixed count assertion requires
24 orders; update that rule when changing row counts.

For controlled invalid cases, choose a separate output folder:

```bash
test-data-agent generate examples/business_rules/dataset_spec.yaml \
  --business-rules examples/business_rules/rules.yaml \
  --seed 12345 --format json --mode mixed --invalid-ratio 0.25 \
  --output out/business-rules-mixed
```

The second command can exit **1** because invalid artifacts intentionally fail
validation. Check `expectations_met`, `unexpected_violation_count` and
`missing_expected_violation_count` in the business report. Selection is seeded,
not an exact 25% of all fields/rule failures; overlapping rules can fail together.
`negative` attempts eligible mutations on every row. Count-only aggregate
assertions are validation-only. A valid baseline is required before injection.

## Four top-level sections

```yaml
field_rules: []       # Per-field checks/defaults
row_rules: []         # Conditions, dates and formulas within one row
cross_table_rules: [] # FK checks and whole-table aggregate assertions
scenarios: []         # Weighted field assignments before field/row rules
```

All four sections default to empty lists. A usable rules payload must contain
at least one rule/scenario; unknown keys are rejected. The standalone format
has no `schema_version` or outer `business_rules` key.

Alternatively embed this same object under `business_rules:` in DatasetSpec.
Do not also supply `--business-rules`: use exactly one rule source. MCP accepts
`business_rules_path` or `business_rules_payload` on its generation/export
interfaces; inspect the installed tool schema for the selected route. For a
review-first agent plan, embed rules before inspecting the final spec and
obtaining approval of its exact fingerprint. Attaching a new rule file after
approval does not make it part of the reviewed specification.

## Every rule and option

The YAML example contains all fields listed below. `table`/`field` names must
match the companion spec; rule files do not declare a database schema.

| Section / type | Required keys | Optional keys and defaults | Execution |
| --- | --- | --- | --- |
| `field_rules` item, no `type` | `table`, `field` | `required: false`, `allowed_values: null`, `min_value: null`, `max_value: null` | Fill missing required values/defaults and repair disallowed membership; numeric bounds are checks, not general clamping |
| `row_rules` / `conditional_required` | `type`, `table`, `when`, `required_fields` | None | For matching rows fill missing required fields from known defaults; validate presence |
| `row_rules` / `conditional_allowed_values` | `type`, `table`, `field`, `when`, `allowed_values` | None | For matching rows select the first allowed value when needed; validate membership |
| `row_rules` / `temporal_ordering` | `type`, `table`, `start_field`, `end_field` | `allow_equal: true` | Validate dates/timestamps and order; basic repair can set end equal to start, so strict order needs suitable generated inputs |
| `row_rules` / `formula` | `type`, `table`, `field`, `expression` | `mode: assign`, `tolerance` described below | `assign` calculates a numeric target; `check` only checks its existing value |
| `cross_table_rules` / `foreign_key` | `type`, `child_table`, `child_field`, `parent_table`, `parent_field` | None | Validate membership in generated parent keys; declare the matching DatasetSpec relationship to generate FK values |
| `cross_table_rules` / `aggregate_formula` | `type`, `table`, `field`, `expression` | `expected: null`, `tolerance` described below | Compare SUM(field), or row count for `field: "*"`, against an expression or explicit expectation; never assign totals |
| `scenarios` item, no `type` | `name`, `weight` | `field_values: {}` | Apply the selected scenario's literal assignments for the current table/row |

`required` means neither `null` nor empty string. `allowed_values` alone does
not require presence. Numeric minima/maxima are inclusive and may be finite
numbers or numeric strings; quote exact decimal endpoints. Required defaults
and repairs are limited: conflicting rules, unsupported types and invalid
baselines fail rather than establishing that any arbitrary rule set is solvable.

## Conditions: the complete `when` grammar

`field` is required. At least one predicate must be supplied:

| Predicate | YAML example | Meaning |
| --- | --- | --- |
| `equals` | `{field: status, equals: cancelled}` | Equality |
| `not_equals` | `{field: status, not_equals: cancelled}` | Inequality |
| `in_values` | `{field: status, in_values: [paid, cancelled]}` | Membership in a nonempty list |
| `gte` | `{field: quantity, gte: 1}` | Inclusive numeric lower bound |
| `lte` | `{field: quantity, lte: 3}` | Inclusive numeric upper bound |
| Explicit null equality | `{field: note, equals: null}` | Logical null; different from omitting `equals` |
| Explicit null inequality | `{field: note, not_equals: null}` | Non-null; empty string still counts as non-null |

Predicates in one block are combined with **AND on the same field**. Use separate
rules for different condition fields. There is no nested `and`/`or`, expression
predicate or arbitrary SQL. The lower bound cannot exceed the upper bound.
Do not serialize both equality keys with null defaults: the loader treats that
legacy pair as omitted predicates. Keep only the intended explicit null key.

## Formula expressions and exact decimals

Supported arithmetic is `+`, `-`, `*`, `/`, unary `-`, parentheses, numeric
constants and field names in the same row. There is no power, remainder, floor
division, comparison, ternary, attribute/index access, `round`, `min`, `max`,
imports or arbitrary Python/SQL. Row formulas cannot call aggregate functions.
Dependencies should already exist when an assignment executes: row rules run
in their listed order. `check` does not repair its target.

For a DECIMAL target, declare `decimal_range` precision, scale and exact string
bounds in DatasetSpec 1.1. Arithmetic uses bounded exact rationals and applies
ROUND_HALF_UP once at the target scale. Use quoted strings for exact decimal
rule bounds and expectations. Ordinary integer/float comparisons default to
absolute tolerance `0.000001`. An **omitted** tolerance on a DECIMAL target means
exact equality after target-scale calculation; an explicitly supplied tolerance
is honored, including `0`. The structural schema's generic default alone does
not describe that type-dependent behavior.

The example assigns `subtotal`, then `total`, then checks `total` with an
equivalent expression. It does not use `check` to derive a new field.

## Aggregate assertions

```yaml
cross_table_rules:
  - type: aggregate_formula
    table: orders
    field: total
    expression: sum('subtotal') - sum('discount') + sum('fee')
    tolerance: 0
  - type: aggregate_formula
    table: orders
    field: "*"
    expression: count()
    expected: 24
    tolerance: 0
```

The left side is always SUM of the named field, or the row count for `"*"`.
The right side is a bounded arithmetic expression with `sum('field')` and
`count()`. Null field values are skipped by sums. Explicit `expected` overrides
evaluation of the expression, but the expression must still pass syntax,
reference and literal checks. Only one table is available: the section name
`cross_table_rules` does not add JOINs, grouping, SQL or references to another
table's rows. Per-parent aggregate mappings belong to DatasetSpec `constraints`,
not this rule type.

## Scenario semantics

Scenario names are unique, weights are positive relative weights and need not
sum to 1 or 100. Weights `3` and `1` mean a probabilistic 3:1 preference, not an
exact quota. One scenario is selected per row independently across tables;
only its `field_values` for the current table are applied. Listing several
tables does not synchronize their rows or create relationships.

Scenarios run first, then field rules and row rules. Later rules can overwrite
scenario values. Scenario selections are not per-scenario quota assertions in
the validation report. Use consistent literals and declare actual relationships
in DatasetSpec rather than attempting to coordinate identifiers with scenarios.

## Limits, safety and maintenance

Only fictional literals belong in examples/rules. Never insert real names,
identifiers, credentials or source contents; sensitive targets/literals remain
subject to the deterministic privacy checks even for numeric formulas and
negative generation. Business rules do not grant source-value preservation.

Current structural limits include 1,000 total rules/scenarios, 255 characters
per identifier, 1,000 allowed values/required fields, 100 tables per scenario,
and 1,024 characters / 128 AST nodes per expression. Payload, expanded YAML,
evaluation-work and deadline budgets apply additionally. JSON Schema does not
replace these checks or executable rule validation.

Regenerate the schema after changing the runtime models:

```bash
python3 scripts/export_business_rules_schema.py
python3 -m pytest tests/test_business_rules_reference.py
```

Read the [task guide](../../docs/how-to/business-rules.md) for the introductory
workflow and the [dataset schema](../../schemas/dataset_spec.schema.json) for
embedding these rules in a complete specification.
