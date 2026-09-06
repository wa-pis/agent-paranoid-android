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
- [x] Commit signed changes, obtain independent review, and merge green PR
  [#490](https://github.com/wa-pis/agent-paranoid-android/pull/490).

## Stage 4 — Release
- [x] Prepare 1.3.2rc1 and collect exact-commit gates and independent approval.
- [x] Obtain Ubuntu preflight artifact hashes and signed acceptance manifest.
- [x] Publish RC1 and verify public Python, container, and documentation artifacts.
- [x] Correct malformed unquoted SQL property-test names discovered during
  stable preparation; keep strict rejection assertions and add explicit examples.
- [ ] Prepare and accept 1.3.2rc2 with unchanged production runtime, repeating
  exact-commit review, all gates, Ubuntu hashes and public verification.
- [ ] Promote accepted RC2 through metadata-only 1.3.2 diff and repeat release gates.
- [ ] Publish and verify stable release; record evidence and archive this change.

RC1 public acceptance: [evidence](../../../docs/release-evidence-1.3.2rc1.md).
