# Fix transformation review boundaries

## Why
Independent AI review of runtime `3c00148c0d2afcf255e7355b6f52bb779d52f70a`
against public baseline `8670e562f50980cfd62678c6f0f51d4887cb8961` found
that common MCP execution could publish after its configured request deadline,
and scalar batch relationship validation treated non-null empty strings as nulls.
The reviewed documentation revision was `d104cab11edb12f3cf80b207b8a6bada66961712`.

## What changes
- Apply the existing shared MCP deadline at transformation checkpoints for
  single review/execution and common review/validation/execution, retaining the
  generation deadline and byte ceilings. Reject before publication, with typed
  value-free deadline errors and identity-limited cleanup.
- Give relationship validation an explicit empty-string null policy. Batch
  transformation selects actual-None-only null semantics; source-free callers
  keep their historical default. Empty strings participate in scalar foreign
  key membership and one-to-one cardinality.
- Add fictional regressions and update the applicable contracts.

## Impact
No activation, release, receipt authority, database/provider access or input
disclosure is granted. Fixes are developed from the registration-closed author
tree. Independent changed-scope review of the final activation/RC SHA remains
required; this change does not retroactively clear the reviewed SHA.
