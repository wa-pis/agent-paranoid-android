# Design: cross-table-negative-cases

## Foreign Keys

Compile each foreign-key rule into an invalid case for its child table. The
case chooses a deterministic key absent from generated parent keys and
preserves a numeric key type when possible. Parent rows are never modified.

## Aggregate Formulas

Compile aggregate rules with a concrete field into invalid cases for their
table. The case changes one selected row's configured field by a finite amount
that makes the aggregate differ from the expected value outside its tolerance.
Other fields and rows remain unchanged.

Rules using `field: "*"` remain validation-only. Adding or removing rows would
create unrelated schema and row-count failures, making the negative case
ambiguous.

## Compatibility

Valid, edge, and load-test modes are unchanged. Negative output values are not
a stable contract; deterministic violation and validation remain the contract.
