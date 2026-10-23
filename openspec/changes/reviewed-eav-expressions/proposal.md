# Change Proposal: reviewed-eav-expressions

## Status
The optional typed formula `when` and source-free EAV target-model slice were
delivered in #648 after the complete local release gate and all 38 applicable
exact-head CI checks passed. Merge commit:
`25a221b70f95a0e9d11e8191a2301dedac9aa690`; acceptance details are recorded in
[tasks.md](tasks.md) and [verification.md](verification.md).
Source-row pivot/unpivot and broader expressions remain separate unimplemented
extensions. No package release or additional source authorization is implied.

## Current support and gap
Conditional-required/allowed-values rules already accept typed predicates.
Before this change FormulaRule supported assign/check without a predicate;
StrictRuleModel rejected the `when` key. The bounded expression AST permits arithmetic and approved
calls, not Python conditional expressions. Scenario weights are probabilistic
assignments and cannot stand in for a predicate. EAV inputs are not automatically
pivoted/unpivoted, and metadata-only discovery cannot recover row-level attribute
relationships. Existing docs correctly require explicit modeled fields/rules.

## Conditional formula contract
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
RC acceptance. Unsupported payload keys and expression syntax remain deterministic rejections.
See design.md for writer conflicts, null semantics and report compatibility.
