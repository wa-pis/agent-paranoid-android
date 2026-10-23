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

After the local gate, final edits only normalize one EOF blank line and strengthen
the existing disabled-report type-reconciliation test (16 interface tests still
pass). Runtime behavior and schemas are unchanged. Provider CI must verify the
complete final commit before merge. Strict docs and Ruff also pass again.
