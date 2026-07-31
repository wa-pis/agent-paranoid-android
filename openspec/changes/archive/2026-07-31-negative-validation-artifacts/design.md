# Design: negative-validation-artifacts

The rule engine records expected validation failures by the stable order of
rules in the validated `BusinessRules` object. Row-level rules increment the
expected count for each injected case. Aggregate-formula rules expect one
validator failure even when several rows are perturbed because aggregate
validation produces one result.

Validation compares those counts with observed failures per rule. Reports
derive unexpected and missing counts without recording the generated values
that caused them. Existing error details retain their global and per-rule
bounds.
