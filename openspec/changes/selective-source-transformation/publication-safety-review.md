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
