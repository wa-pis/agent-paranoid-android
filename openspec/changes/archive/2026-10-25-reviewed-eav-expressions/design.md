# Conditional formula execution design

## Contract and compatibility

Add optional `when: Condition | None` to FormulaRule. Omit it from serialized
rules when absent or null, so existing payloads, fingerprints and seeded output
remain identical. Reuse the existing Condition evaluator and numeric/literal
privacy checks. This adds no Python conditional expression, SQL, source-row
access or new predicate operators.

A missing predicate field in a supplied row is treated by Condition as null;
with a DatasetSpec, unknown predicate field names reject before allocation.
An explicit `equals: null` selects null/missing, `not_equals: null` excludes it,
and numeric ranges reject null/missing as false. A false predicate skips both
assignment and formula expression evaluation. True predicates run the existing
exact DECIMAL or bounded ordinary evaluator; failures remain failures.

Scenarios and field defaults retain their current order. Row rules execute in
reviewed list order, and validation uses the final generated rows. Predicate
fields must not be written by row rules (conditional-required/allowed-values,
temporal repair or assigning formulas), preventing a later repair from changing
which rows a formula selects. Formula targets cannot select themselves.

For a target with multiple assigning formulas, preserve legacy unconditional
behavior when every formula is unconditional. If any assignment is conditional,
require demonstrably disjoint predicates on the same field: equals/in_values
only, no ranges or negation, and no overlapping typed values. Otherwise reject
before generation. Disjoint EAV attribute branches are supported without an
unreviewable last-writer winner. Check-mode formulas do not assign targets.

## Evidence

Conditional formula RuleResult adds optional nonnegative counts only for rules
with a predicate: eligible_row_count is the true-predicate count,
evaluated_row_count counts attempted formula expressions (including evaluation
failures), and skipped_row_count counts false-predicate rows. Existing `passed`
and `failed` retain evaluated outcomes, so skipped rows never inflate success.
No-predicate results omit these new counters to preserve old report bytes.
Zero selected rows reports zero evaluated and all rows skipped, without claiming
source fidelity. Error details remain source-free.

The predicate and expression charge the same explicit GenerationBudget. Static
estimates include predicate membership work; no fresh allowance or deadline is
created at the condition boundary. In mixed/negative mode, a selected formula
violation first uses the existing bounded condition-forcing mechanism, verifies
that it selected the row, then perturbs the target. Existing collateral-failure
and expected-violation accounting remain authoritative; impossible conditions
fail without partial publication.

## EAV target model

Use synthetic `observations` rows with generated entity identifiers, a reviewed
bounded `attribute` enum and native numeric target `value`; authored formulas
may use independently generated operand fields. Attribute vocabulary is not
inferred or preserved from source rows. A generated observation has one
attribute and one value, so no pivot or duplicate-attribute merge occurs.
Missing attributes mean absent observations, while a nullable value is distinct
from an absent observation. Any requested uniqueness over entity/attribute pairs
must be declared and validated explicitly; conflicting source duplicates cannot
be resolved from metadata. A source pivot/unpivot remains a separate I/O and
transformation proposal.

## Required acceptance

Prove old rule/report serialization and hashes unchanged; omitted predicate
seeded output unchanged; true/false/null/missing conditions; skipped division by
zero; exact DECIMAL; schema-bound and schema-less literal privacy; unknown fields;
self predicates, overlapping/disjoint writers and later predicate mutation;
shared work/deadline exhaustion; check-mode no assignment; negative evidence;
CLI publication rollback and unchanged existing output on rejection. Update
business-rule schema, report contracts, EN/RU guidance and full candidate gates
before marking implementation active.
