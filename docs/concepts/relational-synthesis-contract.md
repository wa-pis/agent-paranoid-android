# Relational Synthesis Contract

Relational synthesis preserves reviewed, executable structure. It does not
reconstruct source rows, identifiers, totals, or rare values.

## Preservation Matrix

| Property | Preserved contract | Not preserved | Evidence |
| --- | --- | --- | --- |
| Foreign-key graph | Reviewed parent/child edges, supported cardinality, null policy, and referential integrity | Source key values, row membership, or source ordering | `DatasetSpec` relationships and relationship validation |
| Distribution shape | Configured safe ranges, ratios, bounded categories, and order of magnitude | Exact histograms, rare categories, source totals, or a statistical privacy guarantee | Effective field distributions and validation report |
| Temporal dependencies | Reviewed ordering rules, bounded ranges, and supported lifecycle constraints | Original timestamps, event sequences, or per-source-row timing | Executable temporal rules and business-validation report |
| Business invariants | Supported formulas, conditions, partitions, coverage, foreign keys, and aggregate mappings | Free-form prose rules or unvalidated model conclusions | Effective rule fingerprint and deterministic validation results |

## Approval Boundary

Only reviewed `DatasetSpec` relationships and structured business rules affect
generation. Deterministic mining and AI advisors may propose candidates, but a
proposal has no generation authority. Low-confidence, contradictory, stale, or
unsupported candidates remain review warnings or are rejected.

## Scaling And Privacy

Synthetic row counts and measures may scale while retaining approved relative
shape and order of magnitude. Scaling must use synthetic values and explicit
rules; it must not copy source totals or preserve sensitive outliers. Exact-row
reuse checks are a safety backstop, not proof of anonymity.

Numeric distributions accept a bounded `scale_factor` from `0.1` through
`10.0`. Sensitive numeric distributions require an explicit non-identity
factor; generation scales the approved bounds before drawing values and records
the effective distribution in `dataset_spec.yaml`.

## Publication Rule

A dataset may claim an invariant only when deterministic validation executes
that invariant successfully. Failed or unsupported checks must block valid
publication or appear as explicit controlled-invalid evidence. The manifest,
effective spec, and validation reports form the review record.
