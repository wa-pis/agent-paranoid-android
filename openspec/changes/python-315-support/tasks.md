# Tasks

## 1. Specification

- [x] Inspect declared runtime support, package metadata and CI/dependency matrices.
- [x] Define compatibility scope, promotion gates and preserved safety contracts.
- [x] Validate this proposal with strict OpenSpec and the active-change catalog check.

## 2. Compatibility Investigation

- [x] Verify actual CPython 3.15 release status from official sources (stable; 3.15.2 listed on 2026-11-08).
- [x] Select and record the exact installed stable 3.15 interpreter and build.
- [x] Audit base, every documented extra, `all`, build and test dependencies on existing platforms.
- [x] Record wheel availability, resolver results and upstream blockers with exact versions.
- [x] Select and test dependency markers/profiles where 3.15 needs different minima; preserve 3.11 support.

## 3. Implementation And Evidence

- [x] Add blocking supported 3.15 quality/wheel/latest-all jobs after dependency compatibility is verified.
- [x] Test built-wheel base/extra/all installs and capability checks in isolated environments.
- [x] Run full 3.15 suite and real bounded SDK stdio workflow/recovery contracts.
- [x] Verify both scalable engines, spawn determinism, cancellation, resource limits and atomic publication on Linux/macOS.
- [x] Keep all supported 3.11–3.14 jobs green and review any lock/profile changes.

## 4. Promotion And Delivery

- [x] Record exact source, interpreter, platform, dependencies and executable evidence.
- [x] After stable blocking checks pass, update classifiers, English/Russian runtime/dependency documentation, release guidance, changelog and focused tests.
- [x] Validate OpenSpec and pass the full local implementation release gate.
- [ ] Before a separately authorized RC, complete publication-specific release gates and artifact verification (no RC requested by this implementation task).
