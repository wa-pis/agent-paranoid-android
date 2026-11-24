# Current Development Baseline — 2026-11-25

## Cause

The original optimization work continued on a long-lived local feature branch
based on package 1.5.0 without first checking the authoritative development
branch. A package version, release tag or cached `origin/main` reference is not
evidence that a working branch is current. The preceding port deliberately used
the user-requested 1.7.1 release; the new request changes the default to current
development unless a base is explicitly selected.

## Plan And Completion

- [x] Resolve the remote default and fetch current development; inspect local
  commits, dirty work and divergence before editing.
- [x] Preserve the completed port and merge the fetched development tip without
  resetting, rewriting history or discarding local work.
- [x] Document the default and explicit-base exception in `AGENTS.md` and
  `CONTRIBUTING.md`; retain locked dependencies and existing safety boundaries.
- [x] Run the affected checks and independently verify that the implementation
  and local improvements survive the merge.

## Git Evidence

- The authoritative remote is this project's `origin`; remote HEAD resolves to
  `refs/heads/main`. No `develop` or `dev` branch was advertised.
- Fresh remote/fetched tip:
  `49d12c515c3aa7d012b038c5d1c96b50195fbcc1`.
- Feature branch: `codex/port-local-improvements-1-7-1`.
- Starting feature HEAD:
  `47543ce3e1703a351ea653ba221e3bcb1103c8ca`; clean worktree.
- Initial divergence: one feature-only commit, two upstream-only commits.
- Upstream adds `dd95bd09` and merge `49d12c51`, promoting verified 1.7.1
  documentation. Their diff from v1.7.1 contains eight documentation files,
  38 insertions and eight deletions; no implementation or dependency changes.
- `git merge --no-ff --no-commit` integrated that exact fetched tip. No conflicts
  occurred; the roadmap merged automatically and retains the port additions.
  The merge retains both the port commit and upstream as ancestors.

## Durable Workflow

At each new repository task, resolve and fetch the authoritative development
branch, then record the source SHA, current branch/HEAD, worktree state and
divergence. Merge into a clean feature branch while retaining unpublished work,
or isolate and safely integrate dirty changes before implementation. Do not
silently reset, rebase, stash or discard work to obtain a clean tree.

An explicit user-selected tag, commit or reproducibility baseline takes
precedence. Clarifications and continuation of a task do not trigger another
fetch. An unavailable remote must be reported with the exact available base;
it must not be described as current. Updating source does not authorize an
unrelated package/dependency upgrade. This is a project workflow rule, not a
change to global agent settings or data/approval authority.

## Checks And Limits

- 225 tests passed: all six documentation CI test files, public contract
  fixtures and release-artifact metadata checks.
- Strict MkDocs build passed; no site publication was performed.
- Staged and working-tree whitespace checks passed for this update.
- Independent review confirmed matching workflow rules and unchanged safety
  gates. Separate comparison verified `src`, tests, scripts, CI, dependencies,
  schemas, packaged skills, examples and MkDocs configuration against the port
  commit; there are no implementation changes or unresolved index entries.
- Seven incoming documentation files match upstream exactly; the eighth is the
  roadmap, which retains both upstream release status and our local additions.

The [preceding full verification](verification.md) remains historical evidence
for port commit `47543ce3` (6,236 passed, 25 skipped, 92.24% coverage). Its frozen
code/policy manifest is source-bound; this update adds a workflow section to
`AGENTS.md` and does not rewrite that evidence. The unchanged implementation did
not require repeating the full suite, performance campaign or wheel matrix.
No live database/provider call, transformation approval, tag, push or release
was performed.
