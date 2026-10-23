# Conditional formula candidate verification

The initial 13-case fictional selection/compatibility/conflict matrix produced
12 failures before implementation; the self-target rejection was already covered
by unknown-key rejection. The expanded 27-case matrix passes, including null and
missing semantics, skipped invalid expressions, exact DECIMAL rounding, privacy
with and without a DatasetSpec, unknown fields, overlapping/disjoint writers,
mutated-rule preflight, shared membership work/deadlines, check-mode immutability,
controlled-invalid evidence and CLI rollback with explicit overwrite authorization.
A prior-runtime fingerprint fixture confirms omitted predicates retain the exact
former rules hash, rather than merely comparing two new-runtime payloads.

The independently authored EAV example generates both attribute branches with
12 observations, deterministic replay, exact numeric values and separate skipped
counts. CLI generation publishes a synthetic manifest with no copied source rows.
No source rows, live databases, credentials, providers or source pivot were used.

The first wider run passed 199 tests and correctly rejected stale advisor schema
fixtures in two contract tests. Regenerating public fixtures updates the response
schema; former nonconditional validation-report fixtures remain unchanged.
BusinessRules and DatasetSpec schemas are regenerated. Full release-candidate
checks and provider CI remain pending; this record is not a package release.


Integration review found two further gaps beyond the passing 4631-test candidate:
service assignment counts included skipped rows, and direct schema-less service
calls did not validate predicate literals. Two regressions failed before fixes.
Assignment counters now record actual assignments before controlled-invalid
mutation, so a later forced predicate cannot retroactively count an assignment.
Numeric sampling-bound diagnostics also exclude skipped branches. Public apply
and validation entries enforce predicate privacy before mutation/evaluation.
The expanded 33-case matrix and 165 wider rule/budget/DECIMAL/reference/contract
tests pass; CLI reports assert exactly 12 assignments across the two EAV branches.
The final integrated release gate is pending; the earlier 4631-test result is
not used as evidence for the subsequently corrected integration paths.


Final integrated local candidate: `scripts/check_release.sh` passed with 4636
passed, 23 skipped and 91.97% coverage. Ruff, mypy (156 sources), compilation,
dependency/license compatibility, operational resource budgets, DatasetSpec and
BusinessRules schema freshness and deterministic quickstart all passed. Strict
MkDocs, change and baseline OpenSpec validation passed. Live database integration
was explicitly disabled. The final new matrix contains 33 cases. Provider CI and
merge remain pending; no package publication is authorized or claimed.
