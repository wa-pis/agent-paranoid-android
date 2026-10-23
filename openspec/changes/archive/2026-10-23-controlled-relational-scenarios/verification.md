# Private relational scenario preflight evidence

Base: merged #648 (`25a221b70f95a0e9d11e8191a2301dedac9aa690`).
The immutable declaration and internal compiler are not registered in DatasetSpec,
generation, CLI or MCP and do not activate a partial scenario feature.

32 fictional metadata cases exercise full-edge binding, immutable counts,
strict nonnegative types, explicit seed bounds, canonical spec/size/declaration
identity and stale plans; valid/edge/load rejection of controlled orphans;
mixed/negative admission; exact known eligible totals and all-null outcomes;
one-to-one capacity; bounded repeated-key pool evidence; rejected/unknown/
ambiguous/duplicate edges; unscoped ratio conflicts; native/field/row/weighted
key writers; incompatible foreign-key business checks; mismatched key types;
declaration-count, original work and original deadline limits. Input specs remain
unchanged. No keys, source rows, database calls, providers or file publication
are involved.

123 focused tests passed, including the merged conditional-formula matrix and
existing identifier/budget suites. Ruff and mypy (158 production sources) passed;
strict OpenSpec validation passed. Full release gates will run against the
complete execution candidate before PR/activation. Actual generated snapshot
preflight, allocation, expected-invalid reconciliation, public schemas, examples
and end-to-end acceptance remain open and are not proved by these static tests.

## Private execution follow-up

The private executor allocates only generated key projections, checks actual
sizes/types/null eligibility and exact totals, follows the existing relationship
dependency order, then reconciles scoped and unscoped relationships before any
original mutation. Commit deadline failures restore prior values without
restarting the budget. Evidence contains edge names and counts, never keys.

14 new synthetic execution cases cover deterministic replay, exact nonuniform
fan-out and orphans, one-to-one excess children, frozen all-null masks, malformed
snapshots, actual nullable-total mismatch, deadline rollback, omitted declarations,
dependency chains, late failure of a second target, synthetic string orphan
namespace and projection cell limits. 150 focused cases passed; Ruff and mypy
(158 sources) passed. No live database or public generation call was used.

DatasetSpec registration, report/writer reconciliation, public schemas/docs,
full candidate release checks and exact-head CI/merge remain open. The private
helper is not a shipped end-user feature.

## Complete-contract isolated candidate

The candidate registers reviewed declarations through existing DatasetSpec
loading, Python generation, CLI and MCP consumers. It adds mandatory final
schema/privacy/native/business/scenario checks to generation and writer paths,
including disabled-report cases. Expected controlled-invalid bundles keep
validation_valid false; SQL export retains the valid-FK requirement.

There are 32 preflight, 14 private execution and 16 interface acceptance cases.
The interface suite passes (16 tests); strict whole-source Ruff and mypy (160
sources) pass. The updated advisor response-schema fixture retains all other
13 public fixtures unchanged. Strict MkDocs and all 17 baseline OpenSpec
capabilities pass. Full release checks are running; no CI/merge, package release
or live-server success is inferred from these focused results.

## Full local gate checkpoint

The exact candidate runtime/schema tree passed scripts/check_release.sh:
4698 passed, 23 skipped, 92.03% coverage, plus lint, types, compile, dependency
license/compatibility, direct privacy/SQL boundaries, operational budgets,
schema freshness and deterministic synthetic quickstart. Runtime source/schema
content SHA256: `055faf8ec0b33d2587da416167a3289d1edc560942e896a02751a3fdd3e7b4c6` (sorted relative file names + NUL +
file bytes + NUL for src/**/*.py and schemas/*.json). The isolated runtime binds
this candidate source directly, including subprocesses; no old installed package
was used. TTY-dependent fictional tests ran outside the restrictive sandbox.
Live Trino/PostgreSQL integration remained disabled. The 166-case focused suite,
strict documentation build, change validation and all 17 baseline specifications
also passed. A separate synthetic valid fan-out SQL render retained FK DDL and
COMMIT. Provider CI/merge and public documentation deployment remain pending.

## Review correction before merge

Review identified an unrelated-edge compatibility defect: strict integer/string
scenario-key admission was also applied to ordinary FLOAT/BOOLEAN/DECIMAL edges
in the preview. Three new independent native-edge tests failed before the fix.
The preview now admits existing exact native scalar types with finite-float and
bounded-decimal checks, while selected scenario edges retain their integer/string
contract and empty-key rejection. The three regressions and 169 focused tests
pass, with Ruff/mypy successful. The complete local gate is rerun for this changed
runtime; only the final exact-head provider CI may authorize merge.

## Merged delivery checkpoint after #649

Conditional formulas/source-free EAV modeling merged in #648 as
`25a221b70f95a0e9d11e8191a2301dedac9aa690`. Explicit controlled relational
scenarios merged in #649 as `9b2e02b1e2ad50ce14213b296c32528349578fce`, after
all 38 applicable checks succeeded on exact final head
`534f0ce351761b3dd092159a36e269beaadeb3c9` (five non-applicable publication/tag
jobs skipped). The branch was CLEAN and merged with an exact-head match.

The final full local release gate passed 4701 tests, 23 skipped, with 92.03%
coverage, dependency/resource/schema checks and deterministic synthetic
quickstart. The final candidate and managed runtime/schema trees matched SHA256
`55096093aab2e1cb4276cb3e75aa220202b0d40452c3a19bcd2a09835d787b90`.
The focused suite passed 169 cases, including three reproduced unrelated native
key-type regressions corrected before merge. No runtime changes followed the
final gate.

Documentation run 39942192547 for merged #649 completed successfully. Independent
scripts/verify_documentation.py verification passed against the public site with
expected documentation revision `9b2e02b1e2ad50ce14213b296c32528349578fce`,
including stable/version identity and all four download hashes. The package
identity remains published 1.6.0 (`258c035c22408becf17ab090635710a50dda8ccc`);
new source features are Unreleased. No new package release or live database
acceptance is claimed.
