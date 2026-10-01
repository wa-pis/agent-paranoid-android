# Independent AI review: closed publication boundary

- Reviewer: PublicationBoundary-R1 (Jason), independent AI subagent
  `01a0f8f6-5e7e-7b81-a337-b2476bf458f5`; not author, not human approval.
- Date: 2026-10-01.
- SHA: `1575fcd0b92722b2c85d014be75fbb122fbdafca`.
- Base: `bef20dbe50dc29a18ff2d94b2fac664b02049148`.
- Scope: shared publication diff, canonical snapshots/receipt, effective budgets,
  path-policy dependencies and public activation closure. Static inspection;
  reviewer ran no tests and made no edits or GitHub writes.

## Finding and disposition

Medium: rename commits the directory before parent fsync. Fsync failure reports
failure but staging cleanup misses the renamed destination; subsequent manifest
read can also fail after commit. No demonstrated sensitive-preservation bypass
or partial bundle, but failure/no-publication semantics are not satisfied.

Disposition: blocking prospective public wiring. Candidate fix removes only the
destination matching the captured staging identity on publication failure, and
returns prebuilt manifest metadata instead of reopening it after commit. Other
destinations are never selected for rollback. Independent follow-up review of
the changed scope is required; no approval of the fix is claimed here.

## Executable evidence

`test_publication_fsync_failure_after_rename_rolls_back_own_bundle` fault-injects
only directory fsync after real rename on fictional temporary artifacts.
It fails on installed baseline wheel
`ac0ecb1912138d7ca8ee3177f75eeb7a9ecb777b72b3d7ba3d3836fcf0d9d21b`
because output remains, and passes on candidate source. Candidate executor
suite:287 passed before the typing-only metadata cleanup; focused publication/
command/bundle suite after cleanup:32 passed,255 deselected. Mypy and Ruff pass.
This is a unit fault-injection test, not a client script/product guard bypass.

Public execution and receipt issuance remain unregistered. This review is not
final RC review, release readiness, real-data approval or activation authority.

## Fix follow-up pending

Fix SHA: `2f823678ad3df994fc415a9fca624c65653c93b2`; same independent reviewer
dispatched for the changed scope, no finding disposition received yet.
Fresh installed fix wheel SHA-256:
`16467a0c2b1de68dae312e4b3ac9c88a9f6c41ffc688249f7eca477d7e32abe6`,
`/private/tmp/apa-publication-fix-wheel.YJaOHb/agent_paranoid_android-1.5.0-py3-none-any.whl`.
Installed rollback/receipt-consumption/public-gate focused acceptance: 13 passed,
pytest source-path injection disabled. Development version, not a released RC.

Follow-up received: original finding partially remediated, not closed. Remaining
medium issue: unconditional staging cleanup can fail after successful rename,
outside the rollback-catching try; rollback itself may fail, yet caller receives
the same generic diagnostic while output remains. Identity-checked deletion was
judged safe under the selected local trust boundary; no unsafe-deletion finding.
Reviewer inspected the exact SHA statically, no tests or writes.

Next disposition: omit fallible staging cleanup after confirmed publication;
distinguish retained-output/rollback-failed state using value-free diagnostics;
add executable cleanup/rollback-failure cases and obtain changed-scope review.
Public wiring remains blocked on this technical finding, not a user decision.

Second candidate fix: successful publication no longer reopens staging for
cleanup. If identity rollback or staging removal fails, a distinct value-free
TransformationCleanupError warns that output/staging may remain and requires
inspection before retry. It propagates through the closed command rather than
being collapsed into ordinary failure. Fault tests cover successful publication
with unavailable cleanup and failed post-rename rollback with retained output;
they do not claim OS failure can always be rolled back. Follow-up review pending.

Review at `f5842d84cccad4a2733dcbf2feaf3348c9f91e15`: original fsync/manifest
and post-success cleanup findings remediated, but generic discard helper can
suppress staging identity lookup failures. Remaining medium incomplete-cleanup
reporting finding; no unsafe deletion found. Reviewer ran no tests or writes.

Third candidate fix uses the captured staging identity directly for removal,
without the suppressing discard helper. Failure to obtain initial identity also
reports cleanup incomplete rather than claiming staging removal; no unverified
identity is used for deletion. Fault cases cover initial identity and cleanup
lookup failures with sanitized diagnostics. Follow-up disposition pending.

## Final changed-scope disposition

- Reviewer: PublicationBoundary-R1/Jason, same independent AI subagent.
- Date: 2026-10-01.
- SHA: `3721503e38522fa6966bdc4fd64adbdbecbe3f08`.
- Prior: `f5842d84cccad4a2733dcbf2feaf3348c9f91e15`.
- Scope: staging identity capture, cleanup/error boundary, two new fault phases
  and directly relevant path-policy dependencies; static inspection only.
- Disposition: incomplete-cleanup finding closed; no new findings in changed
  scope. Known identities constrain deletion; lookup failures propagate to a
  sanitized distinct warning. Initial capture failure performs no unverified
  deletion. Successful publication does not reopen staging for cleanup.
- Evidence: exact HEAD/scoped files, diff and initial_identity/cleanup_lookup
  tests inspected. Tests, Mypy, Ruff and diff checks not independently run.
- Limits: no edits/GitHub writes, public activation permission, human approval
  or final RC approval. Prospective public wiring requires its own evidence.

## Shared workflow and total-budget review

- Independent AI reviewer: PublicationBoundary-R1/Jason,
  agent `01a0f8f6-5e7e-7b81-a337-b2476bf458f5`; not the author.
- Date: 2026-10-01 UTC.
- Exact SHA: `3ef89981c72ebfb324e316cf7fed9d80ca70c54a`.
- Scope: changes since `3721503e` in closed local approval/execution,
  workspace-agent candidate wiring, cumulative limits, canonical receipts and
  public read-only review callers. Static inspection only; no edits or writes.
- Finding (low): policy reading used the admitted bootstrap/session limit but
  YAML parsing used the default 512 MiB when no explicit run cap was supplied.
  A larger session cap could therefore produce an inconsistent generic
  rejection. Fail-closed capacity/diagnostic defect, not authorization bypass.
- Disposition: parser now uses the admitted bootstrap limit; two focused unit
  cases pass with session 1 GiB and smaller explicit 8192-byte run cap. Argument
  observation delegates to the real parser; no large allocation or client
  harness product patching. Changed-SHA disposition remains pending.
- No additional reportable safety finding identified. Canonical approval and
  receipt consumption remain separate, workspace paths confined, responses
  value-free, candidate modules unregistered. Prior publication findings remain
  closed. Reviewer inspected acceptance evidence but did not rerun checks.
- Evidence: committed code/tests and progress at the exact SHA; installed
  `/private/tmp/apa-total-workflow-wheel.5vAiaf/acceptance.log` (25 passed),
  `milestone.log` (873 passed, obsolete expectation failed and subsequently
  corrected as recorded in progress).
- Activation still requires matching AGENTS/safety/baseline amendments,
  supported-route and action boundaries (private derive stays unavailable),
  budget precedence/accounting and cleanup-incomplete recovery contract.
  This is neither human approval, activation authority nor final RC review.

### Bootstrap correction disposition

- Independent AI reviewer: PublicationBoundary-R1/Jason, same identity.
- UTC date: 2026-10-01.
- Exact SHA: `c0e1a0ef80ad0cff667a7d7419e515d785e5b48c`.
- Scope: correction and two parameterized unit cases versus `3ef89981`.
- Low finding closed by static inspection; no changed-scope regression found.
  Read and parse share admitted bootstrap.value; later cumulative checks remain.
- Tests establish argument plumbing, not large-policy acceptance. Reviewer did
  not independently run tests, lint, types or wheel execution; no writes.
- Prior closures remain valid. Activation amendment and registration reviews
  remain outstanding; no human approval, activation or final RC claim.

## Inactive activation amendment review

- Independent AI reviewer: PublicationBoundary-R1/Jason, same agent identity.
- UTC date: 2026-10-01; exact SHA:
  `d7a5296bb72f10f5412dbda956669077c1feeb14`.
- Scope: amendment versus `c0e1a0e` in AGENTS, safety model/boundary,
  synthetic-generation and safe-mcp baselines/delta, compared with ADR-0021/0026
  and closed candidate evidence. Static read-only; no checks independently run.
- Disposition: inactive amendment preserves owner-authorized safety boundary.
  One low wording mismatch: explicit run cap may replace default bootstrap
  before policy loading, then must pass the parsed effective-ceiling check.
  Documented that existing behavior; no runtime change or new budget authority.
  Changed-SHA amendment disposition remains pending.
- Before registration: enforce named public action/route subset at the shared
  boundary (private executor supports derive), installed actual CLI/MCP positive
  and negative interface evidence, exact activation-SHA review and required
  branch protections. Closed 25-pass evidence is not public registration proof.
- Evidence: exact amendment diff, accepted ADRs, code and installed acceptance
  log inspected. Dirty progress excluded. Prior parser/publication closures
  unchanged. No human approval, product authority, activation or RC claim.

### Amendment wording disposition

- Independent AI reviewer: PublicationBoundary-R1/Jason, same identity.
- UTC date: 2026-10-01; SHA `67cf8c306f8e4795d2c8c657e349e4a4f79daad8`.
- Scope: bootstrap wording versus `d7a5296` and committed evidence only.
- Low wording finding closed; no changed-scope inconsistency. Explicit-run
  bootstrap, prior session checks and later effective-ceiling validation are
  distinguished, with equality allowed and no automatic elevation implied.
- Static inspection, no repeated code review/tests/writes. Public action/route
  enforcement, installed registration evidence and activation-SHA review remain
  pending. No human approval, activation or final RC authority.
