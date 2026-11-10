# ActivationSafety-R2 / Plato — independent AI review

Date: 2026-10-02. Reviewer agent: `01a0fc87-f221-7823-94fe-b5e5c74b73a7`.
Reviewed HEAD: `343305e28dc5980e54e4ff580419e95e7f650f72`.
Baseline: `bef20dbe50dc29a18ff2d94b2fac664b02049148`.
Tree: `/private/tmp/apa-activation-exact.vWa4be`.

Disposition: **BLOCKED for public activation**. All four findings pending
remediation and independent review of the changed scope at a new immutable SHA.
This records the independent non-author agent's report, not human GitHub approval
or a completed Codex Security plugin scan. No scan ID exists.

## Confirmed findings

### R2-1 — High / P1: typed substitutions reuse sensitive source values

Locations: `src/test_data_agent/io/transformation_source.py:311`,
`src/test_data_agent/io/transformation_execute.py:387` and `:427`.
Sensitive-source reuse preflight selects only ReplaceTextAction. Typed
substitution bypasses it; mapping identity checks compare each pair, while final
whole-row checks compare only the corresponding source row.

Reviewer fictional in-memory reproduction: two sensitive full_name values mapped
to each other. Execution succeeded without a receipt; every output value and
whole output row belonged to the source. SQL/Parquet encoders accepted results.
Requires a valid supplied policy/mapping and review digest, not TTY approval,
forged receipt, classification override or external database.

Recommendation: enforce shared sensitive/unknown source reuse checks for typed
inline/CSV/domain substitutions using bound snapshots and existing budgets;
test cross-row/cross-column reuse and complete-source-row membership before
publication. Do not permit sensitive preservation as a workaround.

### R2-2 — Medium / P2: numeric/binary Parquet sensitivity missed

Location: `src/test_data_agent/adapters/parquet_dataset.py:107`.
Native scalar.as_py values go to infer_sensitive_value_type, which accepts only
strings. Reviewer in-memory Parquet cases: neutral-column integer with an
SSN-shaped representation and binary fictional email were sensitive=false;
equivalent string email was sensitive=true. Requires sensitive content in a
numeric/binary physical type with a neutral name. This demonstrates incorrect
classification, not independent disclosure through ordinary synthetic generation.

Recommendation: explicit type-aware inspection; conservatively classify
unsupported binary evidence. Preserve native matching semantics, retain no values.

### R2-3 — Medium / P2: local profiling deadline ignored

Location: `src/test_data_agent/adapters/parquet_dataset.py:95`.
Inspection constructs GenerationBudget rather than the local profiling budget.
Reviewer configured local profiling to one second and generation to 300 seconds;
selected budget was 300 seconds. Affects inspection exceeding the local ceiling
while within generation/size limits.

Recommendation: use existing local profiling deadline across participating
inspection stages; add fictional clock-driven exhaustion test. No new timeout
guarantee proposed.

### R2-4 — Medium / P2: silent incomplete cleanup on identity mismatch

Locations: `src/test_data_agent/io/transformation_publish.py:68`, supporting
`src/test_data_agent/io/path_policy.py:253`.
Cleanup returns False for both absence and identity mismatch; caller ignores
returns. File-free fault check with failed publication and two False cleanup
results propagated ordinary OSError, not TransformationCleanupError.
Requires failed publication plus concurrent movement/replacement preventing
matching invocation-owned artifact. Actual filesystem race not reproduced.

Recommendation: distinguish verified absence/removal from identity mismatch;
retain identity-limited deletion and sanitized cleanup-incomplete warning.
Existing raised lookup/rollback-failure tests miss the silent mismatch branch.

## Scope, checks and limitations

74 changed files inventoried: 27 runtime, 21 test/fixture, two scripts,
24 policy/document/evidence. Reviewer read changed runtime hunks, supporting
tests/dependencies: receipt TTY issuer and exact-byte binding; CLI/MCP consumer
authority/confinement/source-free separation; all adapter privacy/budgets/
publication; allowed SQL aggregates and remaining restrictions; six Trino auth
methods, HTTPS, secret indirection, OAuth origin guards/diagnostic suppression;
unknown Parquet statistics; invalid-output privacy/exit parity.

Read actual AGENTS.md, SECURITY.md, policy-contract, safety-boundary, relevant
guides and ADR-0021/0026, installed interface acceptance and prior review evidence.
No old reviewer resumed. Out of scope: rerunning historical scale/client claims,
redundant registration payloads/inventory regeneration, release/signatures/CI
approval, unrelated repository-wide audit, private data and live auth/DB/provider.

Actually performed: Git identity/range/status, static tracing, five tiny Python
invocations with fictional in-memory data or file-free fault instrumentation.
No full-suite rerun, edits, commits, push, network, DB, browser or delegation.
Frozen HEAD unchanged and tree clean. Inherited—not reviewer-executed—gates:
2674 passed, 16 skipped, coverage 90.79%, installed interface acceptance five
passed. Intended receipt integrity/consumer separation and unconditional privacy
checks found in static tracing; these do not close findings or prove live auth.

Known client finding 1, synthetic_identifier versus phone/email/SSN validation,
remains open and unfixed. Public activation remains blocked.
