# Tasks

- [x] Bind CI findings to dependency graph and shared runtime; independently investigate compatibility and exposure limits.
- [x] Update only MessagePack lock entry and both shared-runtime OpenSSL packages; extend existing image contract.
- [x] Verify locked audit/licenses, focused compatibility and all three container workloads/scans; obtain independent candidate review.
- [x] Pass exact-head CI, merge, record evidence and archive completed proposal with baseline updates.

## Acceptance evidence (2026-10-29)

- Reviewed implementation: `910d8ae7d21c4e985f33f142ea633e58b4c2b35b`;
  merged in [PR664](https://github.com/wa-pis/agent-paranoid-android/pull/664)
  as `d4beb4416115f42412d2774bd878e3bcc6076eca`.
- Exact-head CI: 38 success, 5 intentional skips. All six final image
  build/workload/scanner jobs (three targets on AMD64 and ARM64) pass in
  [container run40940005425](https://github.com/wa-pis/agent-paranoid-android/actions/runs/40940005425).
  [Python/dependency CI](https://github.com/wa-pis/agent-paranoid-android/actions/runs/40940005245)
  and [docs build](https://github.com/wa-pis/agent-paranoid-android/actions/runs/40940005133) pass.
- Frozen hash-checked dependency audit: no known vulnerabilities; 108 licenses
  accepted. Only MessagePack changes semantically in the lock. Parent focused
  checks: 72 passed; independent candidate review: no actionable finding,
  69 focused tests passed.
- Synthetic malformed-map replay confirms the tested MessagePack1.2.1 leak
  disappears with1.2.3 while strict rejection and valid roundtrips remain.
  Application DTLS exploitability is not established.
- Local full suite: 4,694 passed, 11 failed, 23 skipped. All 11 failures came
  from an environment missing the installed project. Installing the unchanged
  checkout and rerunning those 11 passes; combined coverage92.05%. The remaining
  release-script budgets, schema freshness, seeded synthetic smoke and manifest
  compatibility checks pass. Earlier lint/types/compile/license/direct-API gates
  pass. Live external database integration is disabled locally.
- Local exact Docker build stopped before the changed layer because BuildKit's
  CLI plugin is unavailable; the six successful CI builds provide exact image
  coverage. Existing signed release artifacts remain immutable; this correction
  applies to subsequent builds and does not replace published1.7.0rc1 images.
- Archive uses normal baseline updates for both added requirements; unrelated
  historical feedback, capacity and trust-boundary tasks remain active.
