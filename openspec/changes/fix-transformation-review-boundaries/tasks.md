## Implementation
- [x] Enforce both request and generation deadlines through the shared MCP adapter.
- [x] Preserve typed deadline errors and cleanup-incomplete precedence.
- [x] Select actual-null semantics for transformed scalar relationships.
- [x] Add expiry, cleanup, legitimate-control and null/empty/cardinality regressions.
- [x] Run focused tests and relevant architecture/typing/format checks.

## Delivery
- [ ] Independently re-review changed scope on the final immutable activation SHA.
- [ ] Complete existing RC/CI/public-artifact gates before publication.

Validation: 574 passed, 12 skipped (focused transformation/MCP/architecture suite);
Ruff, mypy (5 changed source files), strict OpenSpec and git diff --check passed.
One independent patch-review cycle found a late rename/fsync deadline gap; the
completion checkpoint and an executable cleanup regression now cover it.
