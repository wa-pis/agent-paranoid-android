# Open questions, superseded prose and implementation gaps

Snapshot: 2026-09-29. This is not a new release checklist and does not turn
unapproved suggestions into required work. Keep three classes separate:
**a product decision is missing**, **an accepted decision is not implemented or
verified**, and **historical documentation needs reconciliation**.

## Decisions not settled by existing authority

| ID | Question | Safe disposition and next authority |
| --- | --- | --- |
| Q-01 | Should different DATETIME spellings/offsets be equal mapping keys because they denote the same instant? | Not implied by field formatting or timezone conversion. Retain unsupported/fail-closed execution where no contract exists; owner must select equality/collision semantics before expanding it. [ADR-0023](0023-field-types-null-time.md). |
| Q-02 | What are nullable internal-formula semantics? | Deferred, **not a 1.6 RC blocker**. Existing private code remains non-public; a future formula feature needs its own contract. [ADR-0026](0026-transformation-scope.md). |
| Q-03 | May a narrow DECIMAL preservation exception override a numeric-shape false positive? | Not active. Provenance of sensitivity evidence must first distinguish shape-only from semantic/content evidence, with exact binding, executable tests and independent review. Do not infer permission from a non-sensitive declaration. [ADR-0008](0008-exact-decimal.md), [ADR-0021](0021-local-preservation-approval.md). |
| Q-04 | May external scripts/API callbacks act as replacement providers? | Unapproved suggestion, not implementation scope. Keep unsupported; owner must explicitly select a trust, data-access and execution boundary before any implementation. [ADR-0022](0022-behavior-policies-mappings.md). |

No approval is requested as part of this documentation task. In particular,
Q-02/Q-04 must not be used to stall already-agreed work. If Q-01 or Q-03 is needed
for a concrete route, identify that route and ask the narrow question then.

## Accepted decisions with remaining engineering evidence

| ID | Remaining work | What must not be claimed |
| --- | --- | --- |
| I-01 | Complete the common transformation core and public wizard/noninteractive/agent execution with existing approval gates. | A private helper, temporary publisher or read-only transform-review is not installed public execution. |
| I-02 | Demonstrate capacity across participating SQL capture, mappings, review, execution and output stages; complete required route evidence. | CSV replacement 300k×50 does not prove SQL scale, all twelve routes or arbitrary-width 1M×100 capacity. |
| I-03 | Finish accepted key/domain/relationship and supported native-type integration. | Type parsing, a domain model or one adapter test is not complete cross-input relationship acceptance. |
| I-04 | Reconcile original client findings and inspect/run only available scripts on fictional baseline/candidate inputs. | Private/unavailable client data and future integration feedback are not passed evidence. |
| I-05 | Complete safety activation evidence, exact-candidate independent review, required GitHub gates and public RC verification. | Accepted architecture and AI evidence do not replace human/platform approval or authorize stable 1.6.0. |

The uncommitted query-limit implementation on `codex/1-6-query-limits` is a WIP
checkpoint with focused evidence in progress.md, not a new approved public
adapter contract. No new hard-RSS/wire guarantee or platform restriction is added
by I-02. Public API details not yet accepted remain design work behind the gate,
not facts reconstructed from private function signatures.

## Known documentary conflicts

| ID | Earlier text | Governing decision and reconciliation |
| --- | --- | --- |
| D-01 | Later sections of policy-contract.md and safety-boundary.md still describe internal totals/formula recomputation as transformation acceptance. | Explicit owner scope correction on 2026-09-28 and [ADR-0026](0026-transformation-scope.md) supersede that requirement. Keep historical/private evidence; do not delete source-free rule support. |
| D-02 | Older policy/report prose describes retention as equality and formatted output percentages as unavailable. | [ADR-0025](0025-action-origin-reporting.md) governs the user-facing three-origin report. Equality safety checks and historical manifest-v1 evidence remain distinct. |
| D-03 | Earlier policy prose treats same-instant DATETIME values as identity replacements, while the later owner clarification explicitly leaves temporal-key equivalence undecided. | Do not promote that sentence into a complete execution contract. Q-01 remains open; the recorded formatting decision does not resolve it. |
| D-04 | Initial-slice policy text says the CSV parser does not change the process-global field limit. | PR #594 introduced scoped coordination/restoration for internal CSV reads. This is stale implementation narration, not a reason to undo accepted scalar-limit support. External unsynchronized changes remain outside the coordination guarantee. |
| D-05 | The general roadmap still names 1.3.x as current work, while release evidence records 1.5.0 and the active change targets 1.6.0rc1. | Use immutable release evidence for shipped status and the active owner-approved plan for current scope. Roadmap reconciliation must not invent dates, integrations or new priorities. |
| D-06 | Historical progress/tasks retain early helper limitations and obsolete blockers. | Use the most recent explicit decision and exact evidence, not the oldest unchecked sentence. A task checkbox is neither authority nor an equal-sized estimate of remaining effort. |

The register preserves these conflicts visibly rather than silently rewriting
history or declaring the entire prose corpus reconciled. The notes added to the
active decision documents point readers here; detailed cleanup belongs to the
next documentation pass for the affected supported behavior.

## Sources

- [Policy contract with dated owner decisions](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/policy-contract.md)
- [Safety boundary](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/safety-boundary.md)
- [Resumption plan](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/resumption-plan.md)
- [Client acceptance](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/client-acceptance.md)
- [CSV scale evidence](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/csv-scale-acceptance.md)
- [Release evidence](../release-evidence-1.5.0.md), [roadmap](../roadmap.md)

