# Resume plan — 2026-09-26

## Current continuation — 2026-10-03

Ordinary implementation automation is ACTIVE in /private/tmp/apa-amended-activation.RVGKRo,
branch codex/1-6-coherent-candidate. Follow progress.md; earlier continuation
states below are historical. Independent validation is blocked and must not be
retried, rephrased or rerouted to evade the platform restriction. Finish available
implementation/contracts/fictional acceptance; pause when only required review
remains. Public activation, merge and release remain gated; stable is unauthorized.

The common CLI/MCP and OAuth registration patches use zero-context hunks. Their
isolated replay requires `git apply --check --unidiff-zero` followed by
`git apply --unidiff-zero` only in the explicitly prepared candidate copy. Ordinary
`git apply` failure is not evidence they are stale. Replay on 3 October produced
exactly the three registration files already used by the installed candidate;
do not apply them to the closed author checkout before independent clearance.

## Current continuation — 2026-10-02

Owner corrected the review cadence: assemble one complete implementation,
documentation, contract and installed acceptance candidate before independent
safety review of its exact activation SHA. Do not resume the incomplete ed24f7b
artifact review or commission reviews of helpers/ordinary commits. Reviewer
capacity does not block candidate preparation; final RC review remains required.
Automation is ACTIVE for this preparation. Earlier pause/next-step statements
below are historical, not the current instruction.

Public execution stays disabled. The unapplied activation-registration.patch
now carries runtime registration, explicit boundary/contract test amendments and
the two additive contract inventories together. Materialize/test it only in an
isolated candidate checkout before the required activation review. Preserve the
unchanged source-free contracts, all other RC routes and acceptance requirements.

## Latest completed private milestone — 2026-09-29

Owner resumed work after the ADR collection. The installed private PostgreSQL
worker → captured-source profile → saved-policy review → temporary CSV route
passed300,000 x50 with full readback and cleanup in217.623s. Only a fictional
injected driver was used; no live database or public activation. Exact wheel,
harness and limits: [postgres-scale-acceptance.md](postgres-scale-acceptance.md).
The next deliverable after this coherent PR is the remaining shared public
interface/activation workflow, subject to existing executable safety evidence
and exact-SHA independent review. Do not repeat accepted scale runs unchanged.
Automation remains PAUSED to avoid overlapping active work.

## Latest completed private milestone — 2026-09-28

Installed-wheel private CSV replacement route passed300,000 x50 (15M cells),
including saved-policy file review, temporary publication, full ordered readback,
mapping precedence/non-cascade, provenance and cleanup. Evidence and exact wheel
digest: [csv-scale-acceptance.md](csv-scale-acceptance.md). This is not public
CLI execution, source preservation, all12 routes or completed RC. Do not repeat
this unchanged run. Next deliverable after this single PR: finish SQL capture/
worker budgets and the remaining shared public interface/activation gates.

## Capacity and diagnostic decision — 2026-09-28

Owner accepted 1,000,000 rows x100 columns target and mandatory 300,000 x50
fictional acceptance. Limit errors must distinguish over-request from runtime
exhaustion and explain how to configure the current session/run and saved profile.
Current 10M-cell and borrowed 10k SQL-profile row ceilings do not satisfy this.
Next: audit/implement effective transformation budgets and real configuration
paths; preserve safe typed diagnostics across worker and public boundaries.
This supersedes the assistant-added hard-RSS/wire release-blocker detour, not
any existing data-protection check. Full original RC scope remains required.

## Owner clarification and resume — 2026-09-28

SQL aggregates are computed by the authorized database query; result columns
are ordinary transformation inputs. Internal formula/total/balance recomputation
is not a required RC feature under the latest owner clarification. Earlier
formula milestones below are historical and superseded for release gating.
Audit original feedback findings 18/23 separately to distinguish existing bugs
from new-feature proposals; do not infer new formula authority from feedback.
Do not delete existing code or expose private derive paths. Formula-null is not
a blocker for remaining SQL-result, mapping, interface and acceptance work.
The owner explicitly requested autonomous continuation and automation resume.

Budget checkpoint: user reports 5% weekly allowance remaining. This document
reconciles existing evidence only; no new implementation, tests, CI or review.
Full 1.6.0rc1 scope remains unchanged. Stable 1.6.0 is not authorized.

## What the 40 open items mean

Numbers below refer to open top-level checkboxes in tasks.md, in file order.
They are navigation numbers, not new tasks. All 40 are covered exactly once.
Four other top-level items are checked. Six nested items are checked and two
remain open. Checkboxes describe acceptance, not units of equal effort.

| Items | Existing evidence / remaining work |
| --- | --- |
| 1–5: contracts | Private policy, exact snapshots, approval helpers and development/activation amendment exist. Final activation review, full artifact/API contract, null/timezone and financial coincidence semantics remain. |
| 6–9, 12, 14: client intake and fixes | Prior inspection, probes and fixes exist for SQL predicates, modes, doctor, Parquet types and older findings. Reconcile exact candidate evidence and remaining cases; do not implement those fixes again. |
| 10, 13: auth and Parquet metadata | Need current decision/evidence audit for Trino auth and unknown-versus-measured metadata. Null-statistics correction alone is not full metadata acceptance. |
| 11: DECIMAL | Private CSV formulas, mappings and synthesis, plus source-free generation/export evidence exist. Full finance semantics, installed-candidate and final acceptance remain. |
| 15–17: client acceptance | Consolidate all 26 findings, then run only missing reviewed baseline/candidate probes. Private/live cases unavailable are not passes. |
| 18–20, 24–26: CSV engine | Exact text and typed mappings, domains, formulas, synthesis, trace and rejection tests exist. Null/temporal behavior, full relationships and end-to-end acceptance remain; these are not six implementations to start over. |
| 21, 27–30: user interfaces | Review/wizard/policy/comment groundwork exists. Public execution and saved-policy parity across CLI/Python/MCP are not complete. |
| 22: user skills | Packaging/discovery and interim offline smoke evidence exist. Full user workflow on installed RC remains. |
| 23: SQL-result access | Separately authorized bounded read path still needs implementation/acceptance audit. Existing aggregate profiling is not this feature. No real DB access. |
| 31: validation/publication | In-memory checks exist. Complete cross-row validation and atomic mixed-origin publication are not complete. Publisher creation was denied by tool approval; do not bypass. |
| 32: retention percentage | Core report and numeric CSV comparison exist, including context-independent rounding. Null/temporal and public output acceptance remain. |
| 33–36: integrated acceptance | Need complete fictional finance fixture, remaining edge cases, rollback and source-free interface regression evidence. Focused helper tests do not close these. |
| 37–39: documentation | Partial updates exist. Finish against actual public contracts, then execute examples and documentation gates once at the milestone. |
| 40: release | Final exact-SHA independent review, required CI, normal merge, RC publication and public artifact verification remain. |

Sources: tasks.md, client-acceptance.md and progress.md; last published code and
evidence checkpoint 7bd752c, documentation commit f815d8d. No new verification
is claimed. Nested development-review checkbox appears stale relative to PR
#576 evidence recorded in progress.md; verify that scope once before checking it,
not by commissioning a duplicate review.

## Next deliverable: one complete CSV user workflow

Owner clarification (2026-09-27): this is the first route, not a CSV-specific
architecture. Full RC requires independent CSV/Parquet/Trino-result/PostgreSQL-
result inputs and CSV/Parquet/SQL-script outputs through one transformation
core. After the CSV baseline, separate adapter concerns and verify all 12
routes; see plan.md. SQL output is a file, not database writes. No live database
authorization or SQL-file import is implied.

Deliver CSV + saved behavior policy -> reviewed local CLI execution -> output
CSV + mixed-origin manifest + value-free retention report. Start with the
already agreed global/per-column exact replacements, not another helper layer.
This is an intermediate milestone, NOT a reduced RC scope.

Acceptance criteria:

1. Fictional fixture uses both global and column rules; column match wins,
   replacements do not cascade, row count/order are retained.
2. The same saved policy passes review and execution; source/policy/mapping
   drift rejects. Preservation, if requested, requires real local interactive
   approval; agents/MCP cannot issue it.
3. Output and manifest appear together only after validation. Failure leaves
   existing inputs/output intact. Reporting contains no source values.
4. An installed candidate CLI runs the documented example without product
   monkeypatches. Record exact SHA, command and result once.
5. Activation follows executable evidence and required independent safety
   review. Do not expose execution merely because the private tests pass.

Update 2026-09-27: owner explicitly confirmed fictional, temporary-test-only
adapter development, without public activation. The private context-managed
adapter allocates its own temporary destination and removes artifacts on exit;
it cannot publish to caller-selected user destinations. This resolves the
development ambiguity, not the public activation gate.

Historical publication-tool denial: existing
AGENTS permits isolated fictional development with temporary test output;
the rejected proposal accepted arbitrary destinations. The subsequent explicit
confirmation permits only the temporary-test-only adapter described above;
it does not authorize arbitrary destinations.

## Decisions and stopping rules

- DATETIME: outstanding question about retaining offsets and same-instant key
  equivalence. Do not infer an answer from automated goal continuations.
- Publication: temporary-test-only development confirmed above. The owner later
  requested autonomous continuation and the heartbeat was reactivated. Pause it
  on a decision/access blocker; public activation and permanent destinations
  remain separate gates.
- Other pending contracts: gather null encoding, financial coincidences and
  remaining auth/metadata choices into one concise decision list at resumption,
  using existing owner decisions first. Do not ask again about HALF_UP or
  DatasetSpec 1.1; both were approved.
- No extra review per ordinary commit/PR. No repeated successful checks without
  changed scope. One coherent implementation batch and milestone report.
- If the next complete deliverable cannot proceed, stop with the specific
  decision needed; do not spend the remaining allowance polishing helpers.

After this CSV milestone: complete remaining typed/finance/relationship and
SQL/interface scope; reconcile all client findings; finish documentation and
installed acceptance; only then final review and release 1.6.0rc1.
