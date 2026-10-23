# Change Proposal: reviewed-eav-expressions

## Status
Proposed follow-up to relational-profile-utility R7. Planning only: this does not
add a formula `when` option, pivot command or broader expression evaluator.

## Current support and gap
Conditional-required/allowed-values rules already accept typed predicates.
FormulaRule supports assign/check but has no predicate field; StrictRuleModel
rejects extra keys. The bounded expression AST permits arithmetic and approved
calls, not Python conditional expressions. Scenario weights are probabilistic
assignments and cannot stand in for a predicate. EAV inputs are not automatically
pivoted/unpivoted, and metadata-only discovery cannot recover row-level attribute
relationships. Existing docs correctly require explicit modeled fields/rules.

## Proposed conditional formula slice
Specify an additive optional typed predicate on FormulaRule, reusing Condition
and its existing literal/name/privacy checks. Predicate false means no assignment
and an explicitly skipped check, never a successful evaluated formula. Define
null/missing field behavior, assign/check ordering, conflict rejection and exact
DECIMAL evaluation before implementation. Keep the expression AST unchanged.
Evidence must separate eligible/evaluated/skipped/failed rows. Both predicate and
formula consume the same deterministic budget and spec/rules fingerprint.

## Separate EAV modeling slice
First require a reviewed source-free target model: entity/key/attribute/value
roles, bounded attribute vocabulary, target native types, missing/null policy,
duplicate-attribute conflict policy and foreign-key identity. Do not infer a
pivot from arbitrary data, select source rows or retain source entity keys.
Generation uses independently generated domains and explicit conditional rules.
Actual pivot/unpivot of existing source rows belongs to a separately authorized
I/O/transformation proposal and cannot be enabled by this synthetic proposal.

## Compatibility and acceptance
Omitted predicates retain current output, rule counts and fingerprints. Public
schema/API/MCP/CLI changes require documentation, safety/privacy regressions and
RC acceptance. Do not silently accept unsupported payload keys while this change
is only proposed; keep current deterministic rejection and recovery guidance.
