# Relational Synthesis Contract

Relational synthesis preserves reviewed, executable structure. It does not
reconstruct source rows, identifiers, totals, or rare values.

## Generated Identifier Domains

Within one dataset specification, identifier fields have separate deterministic
domains, assigned by sorted entity/field names. Integer domains use disjoint
sequences; strings encode the same generated sequence with a synthetic prefix,
not source identifiers or entity labels. Declared relationships subsequently
assign generated parent keys to child fields in dependency order for acyclic
graphs. Cyclic components retain legacy input-order reconciliation; all resulting
relationships must pass validation before publication.
Reordering entities or fields does not change domain numbering or initial
non-null identifier values at a given row position, before relationships and
constraints are applied. Final FK assignments may change with null masks.
Nullable-field masks still consume
order-dependent randomness: changing field/entity order may change which rows
are null. Exact replay requires the same ordered specification.

Replay requires the same specification, seed and algorithm version. Adding or
removing identifier fields can change the domain numbering and generated values.
This is not a persistent mapping across independently generated datasets.
The upcoming 1.6 candidate changes identifier values and their string format;
regenerate fixtures rather than relying on the old row-counter equality.

## Evidence-Bounded Synthesis

The system does not magically discover the complete domain model from a schema
or a sample. It records bounded observations, keeps their provenance, and
turns unverified conclusions into hypotheses that require review.

The conceptual pipeline is:

```text
SourceBundle
  schema + constraints + examples
        ↓
EvidenceProfile
  safe observations + provenance
        ↓
SemanticHypotheses
  candidate relationships and rules
        ↓
human review
        ↓
ReviewedDatasetSpec
  executable generation contract
```

These artifacts have deliberately different authority:

| Artifact | Meaning | Generation authority |
| --- | --- | --- |
| `SourceBundle` | Input schema, constraints, examples, and sampling metadata | None |
| `EvidenceProfile` | Safe observations supported by bounded evidence | None |
| `SemanticHypothesis` | Deterministic or AI-proposed relationship/rule | None until reviewed |
| `ReviewedDatasetSpec` | Explicitly accepted and executable contract | Yes |

### Provenance And Confidence

Every non-declared relationship, distribution, or business rule should retain
an evidence envelope containing, where applicable:

- `origin`: `declared`, `observed`, or `inferred`;
- `status`: `candidate`, `reviewed`, `accepted`, or `rejected`;
- `confidence`: `low`, `medium`, or `high`;
- sample size, sampling method, and time window;
- rows checked and observed violations;
- source/profile fingerprint and explicit assumptions.

Confidence describes how strongly the conclusion is supported by the available
evidence. It is not a claim that the rule is universally true. For example,
observing `invoice.total == sum(lines.amount)` in 200 rows with no violations
supports a medium-confidence hypothesis; it does not prove the domain rule.

AI may rank or explain hypotheses, but it cannot increase their confidence,
change their review status, or authorize generation. Missing evidence remains
unknown and must either be reviewed as an explicit assumption or remain outside
the executable contract.

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

## Validation utility evidence

`validation_report.json` and direct `validate_dataset` results include additive
`utility` evidence bound to the canonical `spec_sha256` used by generation
manifests. Older saved reports without this field remain readable.

- `active_relationships` and `active_temporal_constraints` exclude rejected
  declarations. Their check status is `executed`, `not_declared`, or `not_run`.
  Disabled sections and sections skipped by fail-fast are not executed.
- Relationship sections retain generated parent distinct-key counts, checked,
  resolved and null references. A measured resolution ratio of zero differs
  from `null` when there are no non-null references to check. These counts
  describe generated key domains, not source domains.
- `temporal_metrics` records entity, start/end field, checked row count and
  failed row count for each active native temporal constraint. Empty data has
  zero observations; business-rule evidence stays in `business_validation`.
- `unmodeled_relationship_count`, `source_orphan_ratio` and `source_fanout`
  remain `null`; `source_temporal_fidelity` is `unmeasured`. Source data is not
  inspected by this validator. A valid report proves only the enabled declared
  checks, never complete relationship discovery or measured source fidelity.

Evidence contains metadata and counts, not key values or temporal endpoints.
Collection shares the existing generation work and deadline budget and does
not add a second scan of generated rows or change seeded generation.

## Proposed relational extensions

Existing mixed/negative business rules can create synthetic missing-parent
references. They do not provide an exact orphan-count selector, configurable
fan-out allocation or measured source fan-out fidelity. The separate
[controlled relational scenarios proposal](https://github.com/wa-pis/agent-paranoid-android/tree/main/openspec/changes/controlled-relational-scenarios)
records those optional extensions and their acceptance criteria; no new option
is enabled by that proposal.

Formulas currently support assign/check without a conditional predicate;
conditional-required and conditional-allowed-values rules use predicates.
Scenario weights cannot emulate a predicate. The separate
[conditional formula/EAV proposal](https://github.com/wa-pis/agent-paranoid-android/tree/main/openspec/changes/reviewed-eav-expressions)
records the remaining work. EAV source rows are not automatically pivoted or
retained; explicit target modeling and independently generated key domains
remain necessary.
