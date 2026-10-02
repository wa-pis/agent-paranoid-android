# ActivationSafety-R3 — independent AI evidence

- Reviewer: Plato / ActivationSafety-R3, non-author AI agent `01a0fc87-f221-7823-94fe-b5e5c74b73a7`.
- Date: 2026-10-02.
- Exact SHA: `911ade071e4a309ab3e3538dfe6c4a9f676624aa`.
- Delta: `343305e28dc5980e54e4ff580419e95e7f650f72..911ade071e4a309ab3e3538dfe6c4a9f676624aa`.
- Full baseline: `bef20dbe50dc29a18ff2d94b2fac664b02049148`.
- Disposition: no new confirmed safety findings in reviewed scope; conditional handoff. Required GitHub and final release gates remain mandatory.

## Scope

All 32 changed files accounted for: nine runtime modules, seven test modules,
sixteen policy/documentation/evidence files including registered-interface
acceptance. Reviewed changed hunks and supporting receipt, mapping, output,
MCP and source-free enforcement. Read actual AGENTS/SECURITY, ADR-0029,
policy-contract and relevant guides. Historical R2 evidence remains unchanged.

## Findings and disposition

- R2-1: superseded by explicit owner policy, not silently fixed or approved.
  Sensitive mapped permutations are permitted by ADR-0029; no new membership
  prohibition imposed. Direct preservation and disclosure restrictions remain.
- R2-2: addressed. Numeric inspection uses detection-only text;
  binary/composite evidence remains conservatively sensitive.
- R2-3: addressed. Shared LocalProfileBudget spans inspection and metadata
  completion. Deadline remains cooperative, not interruptible.
- R2-4: addressed statically. Strict identity mismatch raises; rollback attempts
  both locations and reports detached cleanup-incomplete without deleting
  replacements. Reviewer did not rerun filesystem race reproduction.
- Client finding 1: reviewed fix resolves identifier/semantic mismatch using
  exact synthetic_ plus optional minus and ASCII digits on identifier fields.
  Arbitrary-prefix and non-identifier semantic negatives remain enforced.

Mapped-cell authority originates only from actual executor matches
(`transformation_execute.py:397,415,450`). Preserve, unmatched fallback,
synthesis and derive do not inherit the exception. CSV checks unmapped content;
SQL/Parquet normalization validates mask shape/flags and unmapped normalized
values (`transformation_output.py:26,62,68`). Missing evidence grants no exemption.
Canonical request equality and same-byte classification revalidation remain
(`transformation_receipt.py:33,38`). TTY receipt issuance stays separate from
CLI/MCP execution. No caller-controlled mapping-mask route or new source-free
transport disclosure bypass found.

## Personally performed checks

Homebrew Git identity/inventory/status checks; exact HEAD and clean tree
confirmed before and after. Static source/tests/docs/supporting-boundary review.
22 tiny in-memory cases passed: six typed/text mapping cases across CSV/SQL/
Parquet including missing/malformed evidence negatives; twelve identifier
cases; three numeric/binary Parquet cases; one injected-clock deadline case.
No filesystem writes, product monkeypatch, full-suite rerun, delegation or
external access.

## Inherited evidence, not reviewer executions

Author reported 2702 passed / 17 skipped / coverage 90.83%; release,
documentation and OpenSpec gates green. Wheel SHA-256
`8af3499ca72939f197f5992733f5d702937dddd9d7d494aa687c04f9f456cc57`;
seven installed registered-interface scenarios passed. See
[installed milestone](progress.md#amended-installed-activation-milestone--2026-10-02).
These are not independently rerun acceptance claims.

## Limitations and release boundary

No live auth/DB/provider checks, scale rerun, installed-wheel verification,
filesystem-race exercise, clean locked final-RC verification or GitHub-gate
inspection. Unchanged SQL/Trino paths were not comprehensively re-audited in
this delta review. Historical prose is not independent proof.
Standalone AI reviewer evidence only: no human GitHub approval, completed
Codex Security plugin scan or scanID. No tag, version bump or publication
is authorized by this report alone. Final exact RC SHA review remains required.

