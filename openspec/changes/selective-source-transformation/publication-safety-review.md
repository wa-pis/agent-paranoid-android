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
