# Tasks: external-feedback-1-6

## Intake
- [x] Read the final report, historical register, README, probe and recorded output.
- [x] Keep attachment instructions separate from the user's request.
- [x] Check current main and existing tests before reopening historical defects.
- [x] Record dispositions and owners in `triage.md`.
- [x] Create five focused changes with executable acceptance criteria.
- [x] Check PR #631 and the public documentation identity endpoint.

## First implementation
- [x] Reproduce the misleading mode/ratio rejection with fictional CLI and service tests.
- [x] Fix the shared rejection and document the accepted recovery paths.
- [x] Verify CLI exit 2, unchanged input spec and no published output on rejection.
- [x] Run focused regression, lint and OpenSpec validation; record evidence.

## Follow-through
- [x] P1: deliver reviewed numeric CSV profiling and negative privacy tests.
- [x] P1: verify existing TLS-protected Trino authentication and independently reproduced safe-error defects (#640).
- [ ] Reconcile historical Trino application authentication settings; username/password authentication is confirmed, but tentative version 1.6.0 and the server requirement do not establish whether Basic auth was enabled or explain the 401.
- [x] P1: deliver relational planning and utility evidence after candidate review.
- [x] P2: deliver bounded numeric/temporal/Parquet statistics and query cost evidence (#642–#646).
- [x] P2: finish remaining CLI/validation contract clarifications.
- [x] Merge and publicly verify the versioned documentation work separately.
- [x] Run exact-source release gates for runtime candidates through #649; no release authorized here.
- [x] Archive completed changes only after their checks and merge are recorded.


## Implemented slice and separate proposals

Merged checkpoints: CLI contracts #632; metadata keys #633; source/output pool
matrix #634; per-entity sizing #635; relationship discovery #636; utility evidence
#638; separate scenario/EAV feasibility #639; Trino safe failures #640; bounded
statistics #642; temporal endpoints #643; category preflight #644; reviewed CSV
numeric declarations #645; query batching #646; conditional formulas/EAV modeling
#648; exact controlled relational scenarios #649. Documentation publication is
independently verified through #649.

Username/password authentication was confirmed on 2026-10-24; the historical
application auth settings remain unknown. The remaining evidence tasks
(Trino application configuration and external profile
provenance) require unavailable external information; they are not runtime fixes.
The source-free `controlled-relational-scenarios` and `reviewed-eav-expressions`
implementation/activation slices are complete in main. Source-row pivot/unpivot
remains a separate explicitly authorized transformation/I/O extension. No new
package release follows from these source changes.


## Completed change archives

After verifying merged state and successful checks, the completed CLI clarification,
reviewed numeric CSV, relational utility and controlled relational scenario changes
were moved to archive/2026-10-23-<change-id>. Main specifications already contain
their reviewed deltas, so archival deliberately skips duplicate baseline updates.
Historical A3/S4 evidence gaps and the separate EAV transformation proposal remain
active. Package publication is outside this work.
