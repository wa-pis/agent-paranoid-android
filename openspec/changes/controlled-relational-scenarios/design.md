# Controlled relational scenario design

## Typed declaration and prepared identity

`RelationalScenario` names the full parent-entity/field and child-entity/field
edge, exact nonnegative integer `orphan_count` (default zero), and optional
immutable `fanout_counts`. Index i means generated parent row ordinal i;
these are counts, never parent keys, source IDs or a source histogram. Unknown
keys, bool/string/fraction counts and oversized declarations reject. At most
1,000 scenarios and 1,000,000 parent count entries per declaration are admitted;
existing invocation row/work/file/byte ceilings can be stricter.

The internal compiler takes the effective DatasetSpec **after** entity count
resolution and any load multiplier, an explicit signed-64-bit seed and the
existing GenerationBudget. It returns a frozen prepared object with canonical
spec hash, resolved-size hash, declaration hash, seed and immutable declarations.
Reusing it with changed metadata, sizes, declarations or seed rejects before
mutation. These ordinary hashes bind identity; they are not dataset approvals
or a new authority mechanism. Registration will put declarations in the reviewed
spec so existing review/approval fingerprints cover them too.

Specific entity-count overrides retain existing precedence over global --count;
scenarios do not resize entities, multiply counts, silently reduce totals or
reinterpret a supplied histogram after a size change. Omitted declarations must
serialize as absent and leave former hashes and seeded assignments unchanged.

## Static preflight

Select exactly one active declared edge and one writer per child field. Reject
unknown/rejected/duplicate/ambiguous targets and mismatched or unsupported key
types. Initial execution uses matching INTEGER or STRING keys. Fan-out requires
one count per generated parent ordinal. Known repeated-key pools cannot be
mistaken for distinct ordinal keys; non-null uniqueness is rechecked on actual
generated parents before allocation.

Known non-null children have an exact eligible total. All-null children have
zero eligible rows. Intermediate null ratios are not exact quotas: static
preflight checks upper bounds, and the actual frozen generated null mask decides
eligibility before any scenario mutation. Never coerce nulls into keys to make a
requested count fit. Fan-out counts plus orphans must equal actual eligible
children. One-to-one or a primary-key child target permits at most one child per
resolved parent key. Impossible known capacities reject before generation;
unknown generated eligibility rejects before mutation/publication if it does
not match. Zero allocations and all-null outcomes remain distinct from missing
or empty generated entities.

Positive orphan counts require mixed/negative mode. Global invalid_ratio must
be zero with explicit scenarios: scoped exact counts must not silently compete
with unscoped random injection. Negative business-rule injection conflicts with
scoped scenarios; mixed mode with zero global ratio may use compatible ordinary
business assignments. Reject native, field, row or weighted-rule key writers;
positive orphans also reject a conflicting foreign-key business check. Ordinary
check failure still prevents valid publication. These are explicit conflicts,
not silently disabled rules.

## Execution and evidence contract

Keep omitted-scenario paths byte-compatible. For explicit scenarios, generate a
valid synthetic baseline, retain its null mask, and perform allocation in the
existing dependency-ordered relationship pass. This must happen before native
formula/temporal/conditional/aggregate solving and compatible business rules.
Do not first perform ordinary one-to-one allocation: a requested orphan count
may make a larger child table feasible even though the unsplit total exceeds
parent capacity.

Validate the complete generated snapshot, actual non-null distinct parent keys,
nullable eligibility, all target totals and dependency conflicts before mutating
scenario rows. Assign bounded child ordinals to generated parent ordinals using
an independent explicit seeded RNG without shifting ordinary field RNG state.
Create source-free disjoint orphan keys with bounded membership work, including
unique missing keys for one-to-one or primary-key child targets. Charge every
scan, allocation, membership check and mutation to the same allowance/deadline;
never restart a budget in a writer or validator.

Validation evidence must bind to the effective spec/size hashes and identify the
full edge with requested/observed orphan counts and requested/observed generated
fan-out counts. It must distinguish null, checked, resolved and failed references,
record exact expected versus unexpected violations, and keep ordinary relationship
validity false for actual orphans. Matching an explicitly requested invalid
scenario is not a successful valid dataset. Source fan-out/orphan fidelity stays
unmeasured. Mandatory safety and scenario reconciliation run even with optional
validation reporting disabled and after any writer reconciliation. Failed or
stale plans leave existing outputs unchanged and publish no partial manifest.

## Acceptance and current stage

The private compiler and immutable model have 32 new fictional metadata tests;
123 focused tests including merged conditional formulas and existing identifier/
budget suites passed. Ruff and mypy (158 sources) passed on main #648 plus the
private foundation. This foundation is not registered in DatasetSpec,
CLI, Python generation or MCP; no runtime scenario has shipped. Actual snapshot
validation, allocation, evidence, public schemas/docs and full exact-source
candidate gates remain open. Live database/source-row access is neither needed
nor authorized by this design.


Private execution now implements bounded generated-key previews, dependency-order
allocation, count-only observations and atomic commit with deadline rollback.
Its 14 new synthetic cases and 150 focused regression tests pass. Public
registration and mandatory export/report reconciliation remain unimplemented;
this private result does not prove public activation or publication safety.
