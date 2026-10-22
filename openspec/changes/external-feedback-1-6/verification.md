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
