## Implementation
- [x] Enforce both request and generation deadlines through the shared MCP adapter.
- [x] Preserve typed deadline errors and cleanup-incomplete precedence.
- [x] Select actual-null semantics for transformed scalar relationships.
- [x] Add expiry, cleanup, legitimate-control and null/empty/cardinality regressions.
- [x] Run focused tests and relevant architecture/typing/format checks.

## Delivery
- [x] Independently re-review changed scope on the final immutable activation SHA.
- [x] Complete existing RC/CI/public-artifact gates before publication.

Validation: 574 passed, 12 skipped (focused transformation/MCP/architecture suite);
Ruff, mypy (5 changed source files), strict OpenSpec and git diff --check passed.
One independent patch-review cycle found a late rename/fsync deadline gap; the
completion checkpoint and an executable cleanup regression now cover it.

## Final evidence reconciliation — 2026-10-25

The final stable activation/promotion was independently reviewed at 258c035c22408becf17ab090635710a50dda8ccc and publicly accepted in 39018919261; see docs/release-evidence-1.6.0.md for genuine fictional controlling-terminal evidence and limits. Transformation implementation files remain unchanged between that stable tag and 1.7.0rc1. Fresh exact-main review (PR #655), four main gates, Ubuntu preflight and all 12 public checks (40173739663) accepted the new release. This reconciles completed historical activation; it is not a new preservation approval or live acceptance.

[1.7.0rc1 release evidence](../../../../docs/release-evidence-1.7.0rc1.md) records exact source, hashes and actual workflow identities. Earlier pending checkpoints retain their original historical meaning.
