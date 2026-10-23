# Contract clarification evidence

Existing CLI/parser/presenter and business-rule regressions pass, including the
quickstart golden path from a disposable checkout. Shared I/O tests cover mixed
and negative effective modes/ratios in manifests and unchanged input specs;
new external-feedback tests cover explicit zero ratios for valid/edge/load_test.

Code audit retains existing contracts: infer-spec describes a profile input and
spec output; DatasetSpec generation names a bundle folder; single-CSV output
retains its file contract. Qualified local-category scopes remain intact in
`test_local_category_parser_preserves_qualified_entity_scope`. Formula assignment
errors include table/field in `rules/engine.py`; no raw input value is appended.
RC4's `test_sql_load_count_is_materialized_once` verifies explicit count overrides
load multiplication, including exported rows. JSON errors remain one structured
document with the existing category and no stderr duplication.

Public guides now clarify sampling ranges versus enforced rules, assign/check,
probabilistic scenario weights, EAV limits and ordered-spec/version/environment
seed replay. Runnable business-rule reference tests passed. No algorithm or
generation semantics changed for these clarifications.

Focused evidence is shared with external-feedback-1-6/verification.md and
reviewed-numeric-csv-profiling/verification.md. Passing these checks does not
publish a runtime release or archive this change before merge.
