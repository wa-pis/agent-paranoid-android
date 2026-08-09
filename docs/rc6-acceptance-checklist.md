# RC6 Acceptance Checklist

This checklist applies to the immutable `1.0.0rc6` tag. Local wheels and
source checkouts are not substitutes for the public-artifact checks.

## Source and review identity

- [ ] RC6 tag points to the reviewed fixed commit.
- [ ] Independent security review records reviewer identity or stable
  pseudonym, commit, UTC date, scope, findings/disposition, and signature or
  approval URL in the [review evidence](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/1-0-0-rc6-final-release-candidate/security-review-evidence.md).
- [ ] RC5 is treated as historical and superseded for stable promotion.

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
- [ ] RC6-S12: CI classification uses trusted code, release publication checks
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
- [x] Synthetic regression tests cover category reordering, placeholder-shaped
  literals, ordinary and typed constructor/provider/validation failures,
  dynamic exception-class markers, incomplete status, formatted traceback
  output, direct exception-chain inspection, source-free common categories,
  sensitive numeric profiles, provider formulas, bounded generator transport,
  JSON structural limits, safe artifact names, CSV formula injection,
  request-cap exhaustion, backend-error redaction, opt-in row privacy,
  semantic-provider timeout/replay/output policy, filesystem races, interrupted
  publication, overwrite approval, and terminal escaping.
- [ ] Independent review is rerun against the exact fixed RC6 commit and every
  finding has a closed or explicitly approved disposition.

## Public Python artifacts

For each profile, install the public wheel in a clean environment and run the
literal README commands plus `test-data-agent --version`, `demo`, and `doctor`.

| Profile | Status | Evidence |
| --- | --- | --- |
| base | [ ] | |
| `parquet` | [ ] | |
| `mcp` | [ ] | |
| `trino` | [ ] | |
| `mcp,trino` | [ ] | |
| `openai` | [ ] | |
| `all` | [ ] | |

- [ ] Public wheel and sdist match the release commit and version.
- [ ] Checksums, SBOM, provenance, attestations, and signatures are published
  and independently verified.
- [ ] Each public profile is installed with `--require-hashes` against the
  independently verified wheel digest.
- [ ] Upgrade from public `0.12.0` succeeds without changing the README
  commands and uses hash-pinned dependencies plus verified old and new wheels.

## Public containers

- [ ] CLI image: version, doctor, demo, signature, SBOM, and digest verified.
- [ ] Generator MCP image: version, health check, signature, SBOM, and digest
  verified.
- [ ] Trino MCP image: hardened configuration, health check, signature, SBOM,
  and digest verified.

## Quality gates

- [ ] Full unit/integration test suite, coverage threshold, lint, typing, and
  compile checks pass.
- [ ] Release script and strict documentation build pass on the exact RC6
  commit.
- [ ] Stable promotion uses only the accepted RC6 source tree plus reviewed
  release metadata changes.
