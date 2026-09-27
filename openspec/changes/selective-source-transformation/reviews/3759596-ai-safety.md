# Independent AI safety review — private Parquet input

- Reviewer: Boyle / CSV-Gate-1, agent 01a0dfa0-7f22-75d3-9b19-d181e11f187d.
- Date: 2026-09-27 (Europe/Samara).
- SHA: 3759596b49ecaa8b59b39a9b6b4feef7bb49bc20.
- Base: 65424ced6d1184aa1aa183834325c08e277e24c8.
- Submission: 01a0e39d-3aa0-7b53-8dc4-ce420bf8b32f.
- Scope: private Parquet decoder, native matching/formatting, source reuse,
  nullable output, exact-byte snapshot binding. Concurrent documentation excluded.
- This is AI review, not human approval or release/activation authorization.

## Findings and disposition

1. **High, open: decoded expansion exceeds metadata limit.** Encoded-page
   uncompressed size does not bound dictionary expansion into retained Python
   rows. Reviewer probe: 2,048 repeated 4,096-character fictional strings;
   17,011-byte file, 12,349 metadata uncompressed bytes, 8,388,608 decoded string
   bytes accepted under a process-local 1 MiB expanded limit. Add cumulative
   decoded accounting and bound expansion before Python materialization.
2. **Medium, locally fixed; re-review pending:** native null's empty intermediate
   spelling caused whole-row preservation rejection for genuine empty -> null.
   Probe: nullable string column [empty, null] mapped to [null, filled]; review
   passed, execution rejected. Logical null-state comparison now replaces the
   textual guard; standalone fictional publication regression passes.

## Checks

Reviewer inspected diff and focused tests and ran only the two bounded in-memory
fictional probes. No product edits, network, live data, receipts or publication.
The author's 363 tests/mypy results were not independently rerun. No additional
sensitivity or snapshot-binding regression identified; not an exhaustive claim.
Author's medium-fix selection: 18 tests passed (new regression and identity/
preservation guards); Ruff passed. High remains open; no PR or activation.
