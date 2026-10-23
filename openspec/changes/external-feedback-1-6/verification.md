# First implementation evidence — 2026-10-22

Base: main `5ada03f9b372c2c633a1207b550327121e6bebf4`.
Runtime change: shared mode/ratio recovery text only. Generation, privacy,
authorization and output semantics are unchanged.

## Reproduction and results

- The original text failed six new fictional CLI/service recovery assertions.
- The final regression file covers human and JSON rejection, exit 2, stable
  `invalid_input` classification, no output, unchanged service input and accepted
  explicit zero ratios across valid, edge and load_test modes (12 cases).
- Combined focused run: 332 passed, one skipped (isolated OAuth registration
  candidate unavailable), one deselected. Suites: external feedback, documentation,
  RC4 feedback, CSV, SQL query profiling, PostgreSQL/Trino builders, Trino auth/OAuth
  CLI, CLI/presenter, I/O workflows and business-rule reference.
- The deselected quickstart golden test rejects its fixture path under the
  managed `.codex` worktree as an unsafe filesystem path. The unchanged test
  passes in the primary checkout. This is separate from mode/ratio validation.
- Earlier focused identifier-pool/RC3 and business-rule checks also passed.
- Ruff on changed Python files and `git diff --check`: passed.
- All six new OpenSpec changes: strict validation passed.
- MkDocs: strict build passed. A local build is not publication evidence.

The initial JSON regression expected the parser's `invalid_arguments` category;
it was corrected to the existing service `invalid_input` contract without changing
production classification.

## Feedback verification

- Independently constructed positive fractional measures remain classified as
  sensitive phone-like strings by both standalone and streaming CSV profilers.
  Only classification metadata was inspected; no report rows became fixtures.
- Current main already has zero/subunit numeric-shape metadata and Trino runtime
  authentication. Existing regression suites were rerun; these are verification
  and evidence-reconciliation tasks, not missing-feature implementations.
- Missing external profile version/configuration and live server behavior remain
  unknown. No live database, external probe, full release gate or package
  publication was run.

## Documentation state

PR #630's business-rule reference was merged. PR #631's versioned documentation
remains separate and open at intake. The public root responds, but the new
`documentation.json` identity endpoint returns HTTP 404. Do not mark the new
documentation published until merge, deployment and public identity/export
verification succeed.

Follow-up: publication completed through merged #631, revision
`d10145be9f01085eb1648b7192045ab020095b20`, Documentation run 39842360108.
Independent `scripts.verify_documentation` passed against the public site with
that expected identity, including stable/version aliases and all download hashes.

## Merged delivery checkpoint after #649

Conditional formulas/source-free EAV modeling merged in #648 as
`25a221b70f95a0e9d11e8191a2301dedac9aa690`. Explicit controlled relational
scenarios merged in #649 as `9b2e02b1e2ad50ce14213b296c32528349578fce`, after
all 38 applicable checks succeeded on exact final head
`534f0ce351761b3dd092159a36e269beaadeb3c9` (five non-applicable publication/tag
jobs skipped). The branch was CLEAN and merged with an exact-head match.

The final full local release gate passed 4701 tests, 23 skipped, with 92.03%
coverage, dependency/resource/schema checks and deterministic synthetic
quickstart. The final candidate and managed runtime/schema trees matched SHA256
`55096093aab2e1cb4276cb3e75aa220202b0d40452c3a19bcd2a09835d787b90`.
The focused suite passed 169 cases, including three reproduced unrelated native
key-type regressions corrected before merge. No runtime changes followed the
final gate.

Documentation run 39942192547 for merged #649 completed successfully. Independent
scripts/verify_documentation.py verification passed against the public site with
expected documentation revision `9b2e02b1e2ad50ce14213b296c32528349578fce`,
including stable/version identity and all four download hashes. The package
identity remains published 1.6.0 (`258c035c22408becf17ab090635710a50dda8ccc`);
new source features are Unreleased. No new package release or live database
acceptance is claimed.
