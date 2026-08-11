# RC6 Acceptance Checklist

This checklist applies to the immutable `1.0.0rc6` tag. Local wheels and
source checkouts are not substitutes for the public-artifact checks.

The immutable public results are recorded in the
[RC6 published release evidence](release-evidence-1.0.0rc6.md).

## Source and review identity

- [x] RC6 tag points to the reviewed fixed commit.
- [x] Independent security review records reviewer identity or stable
  pseudonym, commit, UTC date, scope, findings/disposition, and signature or
  approval URL in the [review evidence](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/1-0-0-rc6-final-release-candidate/security-review-evidence.md).
- [x] RC5 is treated as historical and superseded for stable promotion.

## Security review closure

- [x] PR #331 suppresses provider text from normal formatted tracebacks.
- [x] PR #332 reserves placeholder-shaped baseline literals from generated
  placeholder collisions.
- [x] PR #333 replaces incomplete provider status with a fixed local reason.
- [x] PR #334 detaches handled OpenAI failures from their cause/context chains.
- [x] PR #335 preserves rare-category replacement and placeholder provenance
  across reordered baselines.
- [x] PR #336 replaces dynamic provider exception names with fixed text and
  contains every ordinary SDK constructor exception.
- [x] RC6-S1: reordered baseline categories cannot leave an original rare value
  in the sanitized profile, baseline, or serialized advisor request.
- [x] RC6-S2: handled provider/validation failures have empty `__cause__` and
  `__context__`, and their public messages use only fixed local allowlisted
  text rather than dynamic Python exception class names.
- [x] RC6-S3: every ordinary SDK constructor exception, including exceptions
  outside `OpenAIError`, becomes the fixed local `ValueError` with no raw text,
  `__cause__`, or `__context__`.
- [x] RC6-S4: incomplete responses use a fixed bounded local reason and never
  reflect raw provider status text.
- [x] RC6-S7: external advisor requests contain no raw categorical values,
  including common names or address-like values missed by heuristics.
- [x] RC6-S8: sensitive numeric Trino profiling suppresses exact extrema and
  percentiles in MCP responses, profiles, specs, and planning artifacts.
- [x] RC6-S9: advisor-proposed constraints reject string constants, unknown
  references, and sensitive targets; post-solve privacy/type validation runs
  before publication.
- [x] RC6-S10: generator MCP enforces pre-parse raw-frame, shared invocation,
  and final-response budgets; JSON structural limits apply before full
  materialization.
- [x] RC6-S11: public artifact names are safe path components, CSV formula
  markers are neutralized, and formula/validation diagnostics are bounded.
- [x] RC6-S12: CI classification uses trusted code, release publication checks
  signed tag and accepted commit identity, and RC acceptance is machine-
  enforced.
- [x] RC6-S13: active MCP requests and shared Trino work are globally bounded;
  cancellation, disconnect, timeout, and teardown release state exactly once.
- [x] RC6-S14: Trino driver errors are fixed and redacted, and catalog/schema
  enumeration has an explicit tested metadata-exposure policy.
- [x] RC6-S15: the explicit opt-in `run_safe_select` has a separately
  documented and
  enforced row-privacy contract, including names, addresses, and heuristic
  false negatives; default aggregate-only tools remain a separate surface.
- [x] MT-01: bounded nested maps, arrays, and rows apply the same string and
  sensitive-value masking before `run_safe_select` returns them.
- [x] RC6-S16: semantic-provider calls have bounded timeout/cancellation,
  deterministic replay or a seed-bound fingerprint, synthetic-only identity
  output, and post-generation privacy/type checks.
- [x] RC6-S17: filesystem publication and overwrite paths reject symlink and
  TOCTOU attacks, use no-follow/inode validation, and revalidate before
  publication and cleanup.
- [x] RC6-S18: single-entity publication has completion/read-validation
  semantics and sibling-artifact replacement requires explicit approval;
  interrupted and collision cases are covered.
- [x] RC6-S19: untrusted metadata, paths, and errors are escaped and bounded
  in CLI and log output, with control-character injection regressions.
- [x] RC6-S20: deployed branch/tag rulesets, required checks, and PyPI Trusted
  Publisher approvals are recorded as external acceptance evidence.
- [x] FS-01: CSV-folder profiles, caches, specs, and generated rows contain
  collision-safe ranked labels instead of source-derived text categories;
  inferred conditional rules use the matching labels.
- [x] AG-01/FS-02: provider-bound profile and baseline constraints replace
  `equals`, `not_equals`, and `in_values` strings with the matching
  field-scoped category labels; unrepresented strings fail closed.
- [x] AG-03: provider-bound integer, float, boolean, and null categories use
  typed field-scoped labels while ordinary numeric bounds remain unchanged.
- [x] SC-08: the Dockerfile frontend is pinned to the immutable OCI index
  digest for the reviewed `docker/dockerfile:1.7` release.
- [x] FS-03: single-CSV generation checks complete-row reuse against digests
  captured during the exact profiling read, including atomic path replacement.
- [x] FS-06: dataset specs and writers reject entity names reserved for control
  artifacts before any output file is created.
- [x] FS-08: dataset-row readers reject duplicate entity stems across supported
  artifact formats before reading any row file.
- [x] FS-10: local CSV profiling checks its monotonic deadline between field
  processing and finalization operations.
- [x] MT-04: audit capacity rejects new invocations before execution unless a
  bounded terminal record can be retained.
- [x] AG-04, FS-11, MT-02, and MT-03: exact Low finding identities, risk owner,
  rationale, revisit triggers, and post-1.0 target are recorded in
  [Known Issues](known-issues.md).
- [x] Synthetic regression tests cover category reordering, placeholder-shaped
  literals, ordinary and typed constructor/provider/validation failures,
  dynamic exception-class markers, incomplete status, formatted traceback
  output, direct exception-chain inspection, source-free common categories,
  sensitive numeric profiles, provider formulas, bounded generator transport,
  JSON structural limits, safe artifact names, CSV formula injection,
  request-cap exhaustion, backend-error redaction, opt-in row privacy,
  semantic-provider timeout/replay/output policy, filesystem races, interrupted
  publication, overwrite approval, and terminal escaping.
- [x] A disposable synthetic PostgreSQL check proves the profiling role cannot
  write, applies mandatory schema/table/column allowlists and budgets, preserves
  only the approved enum, validates generated rows, executes the deterministic
  SQL file in an empty target, and leaves zero FK violations.
- [x] Public documentation distinguishes default replacement, selective local
  preservation, external/default-MCP egress boundaries, generic SQL output,
  and executable PostgreSQL export, with runnable CSV/PostgreSQL/Trino examples.
- [x] Independent review is rerun against the exact fixed RC6 commit and every
  finding has a closed or explicitly approved disposition.

## Public Python artifacts

For each profile, install the public wheel in a clean environment and run the
literal README commands plus `test-data-agent --version`, `demo`, and `doctor`.

| Profile | Status | Evidence |
| --- | --- | --- |
| base | [x] | [Verify Published Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31526588778) |
| `parquet` | [x] | [Verify Published Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31526588778) |
| `mcp` | [x] | [Verify Published Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31526588778) |
| `trino` | [x] | [Verify Published Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31526588778) |
| `postgres` | [x] | [Public PostgreSQL profile evidence](https://github.com/wa-pis/agent-paranoid-android/issues/398) |
| `mcp,trino` | [x] | [Verify Published Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31526588778) |
| `openai` | [x] | [Verify Published Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31526588778) |
| `all` | [x] | [Verify Published Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31526588778) |

- [x] Public wheel and sdist match the release commit and version.
- [x] Checksums, SBOM, provenance, attestations, and signatures are published
  and independently verified.
- [x] Each public profile is installed with `--require-hashes` against the
  independently verified wheel digest.
- [x] Upgrade from public `0.12.0` succeeds without changing the README
  commands and uses hash-pinned dependencies plus verified old and new wheels.

## Public containers

- [x] CLI image: version, doctor, demo, signature, SBOM, and digest verified.
- [x] Generator MCP image: version, health check, signature, SBOM, and digest
  verified.
- [x] Trino MCP image: hardened configuration, health check, signature, SBOM,
  and digest verified.

## Quality gates

- [x] Full unit/integration test suite, coverage threshold, lint, typing, and
  compile checks pass.
- [x] Release script and strict documentation build pass on the exact RC6
  commit.
- [ ] Stable promotion uses only the accepted RC6 source tree plus reviewed
  release metadata changes.
