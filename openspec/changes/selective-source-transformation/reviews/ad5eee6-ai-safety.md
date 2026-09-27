# Temporal preservation — independent AI conformance review

- Identity: Boyle / CSV-Gate-1, independent from author.
- Date: 2026-09-27, Europe/Samara.
- Initial SHA: 447fd4e0e1189e4bc1f22a763a389545048925fd.
- Re-reviewed SHA: ad5eee6f693207c673f2b3ce225ceab8996b3f63.
- Evidence: [reviewer task](codex://threads/01a0dfa0-7f22-75d3-9b19-d181e11f187d),
  submissions 01a0e1c3-59f9-7061-81fb-5fedf6b5c15e and
  01a0e1cc-c2e1-7240-ac9f-ff4faf202159.
- Scope: temporal field rendering, explicit preservation formatting, receipt
  and whole-row boundary, retention reporting, focused regressions and contract.

| Finding | Severity | Disposition |
| --- | --- | --- |
| Formatted preservation plus unmatched preserve retained a whole row | High | Resolved: actual preserved fields tracked per row across direct and both fallback branches; checked before output append. |
| Repeated input directives escaped as re.error with private pattern | Medium | Resolved: duplicate input directives reject; regex errors become fixed detached boundary errors. |

Reviewer confirmed both fixes, no new changed-scope findings. Initial checks
were static inspection and narrow fictional in-memory probes. Re-review was
static diff/control-flow/regression inspection; author's 229 passing tests and
Ruff were not independently rerun. Author additionally reproduced whole-row
publication failure through a fictional PTY receipt before the fix.

No reviewer edits, network, real data, receipts, publication or activation.
Earlier resolved findings and deferred scope were not reopened. This is AI
conformance review, not human/GitHub approval or authorization to activate/release.
Public/durable execution, complete financial/relationship and installed RC
acceptance remain outside this narrow completion claim.
