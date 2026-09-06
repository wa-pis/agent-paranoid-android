# Tasks: generation-contract-hardening

## Stage 1 — Executable semantics
- [x] Record reproduced defects, scope, compatibility, and release sequence.
- [x] Exclude rejected rules and order formula dependencies with cycle checks.
- [x] Preserve nullable foreign keys and validate required identifiers.
- [x] Honor total generated string length bounds.

## Stage 2 — Validation and publication
- [x] Share row privacy checks across generation and revalidation.
- [x] Enforce complete valid-mode checks before returning or publishing rows.
- [x] Cover post-business-rule mutation and all artifact publication paths.

## Stage 3 — Acceptance
- [x] Add regression tests, including interacting rules and adapter failures.
- [x] Update canonical specs, user documentation, migration notes, and changelog.
- [x] Run full release gate and strict documentation build (1289 passed,
  10 live-service skips; 90.34% coverage).
- [x] Complete security review of the immutable implementation diff; correct
  the discovered numeric-string regression and rerun the full gate.
- [ ] Commit signed changes, obtain independent review, and merge green PR.

## Stage 4 — Release
- [ ] Prepare 1.3.2rc1 and collect exact-commit gates and independent approval.
- [ ] Obtain Ubuntu preflight artifact hashes and signed acceptance manifest.
- [ ] Publish RC and verify public Python, container, and documentation artifacts.
- [ ] Promote accepted RC through metadata-only 1.3.2 diff and repeat release gates.
- [ ] Publish and verify stable release; record evidence and archive this change.
