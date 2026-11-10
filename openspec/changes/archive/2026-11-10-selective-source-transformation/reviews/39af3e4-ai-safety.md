# Independent AI re-review — private Parquet input fixes

- Reviewer: Boyle / CSV-Gate-1, agent 01a0dfa0-7f22-75d3-9b19-d181e11f187d.
- Date: 2026-09-27 (Europe/Samara).
- SHA: 39af3e4ccb4bf6979552ad214f1501dc08465313.
- Base: 3759596b49ecaa8b59b39a9b6b4feef7bb49bc20.
- Submission: 01a0e3aa-4b74-77e0-bd9b-f9e77098ec6c.
- Scope: only the two open findings in [initial review](3759596-ai-safety.md).

## Disposition

High decoded expansion finding resolved for cumulative decoded-payload
enforcement. Accumulated batch.nbytes rejects dictionary expansion and
cross-batch overflow before to_pylist and row retention. Three isolated
regressions cover acceptance, cumulative rejection and first-batch rejection.

Residual limitation: Arrow allocates each batch before this check. Retained
Python object overhead and conversion allocations are outside batch.nbytes.
Transient memory exhaustion remains possible. This is not a peak-RSS bound;
hard containment requires separately enforced allocation/process limits.

Medium null/empty confusion resolved. Logical null-aware tuples permit real
empty-to-null changes while preservation/native-equivalence guards remain.
The new publication regression asserts [None, filled] values.

No additional changed-scope defect identified. These findings no longer block
private activation-design handoff under the decoded-payload guarantee.

## Evidence and limitations

Static diff, control-flow and regression inspection only. Author-reported tests
were not independently rerun. Scoped code/tests matched SHA; concurrent docs
excluded. No edits, network, live data, receipts or publication. Unrelated
closed scopes not reopened. AI review, not human approval or activation/release
authorization. Full RC scope remains incomplete.
