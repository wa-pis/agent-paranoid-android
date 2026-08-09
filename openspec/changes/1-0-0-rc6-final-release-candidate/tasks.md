# Tasks: 1-0-0-rc6-final-release-candidate

## Runtime hardening

- [x] Make rare-category placeholders deterministic, field-scoped, unique, and
  collision-free against normal categories and other placeholders.
- [x] Add tests for normal-category collision, equal rare values in different
  fields, repeat determinism, and structural-identity preservation.
- [x] Add `StructuredCompletionResult[T]` and per-call metadata on successful
  OpenAI calls.
- [x] Attach bounded metadata to preflight, provider-error, incomplete, and
  invalid-response failures without exposing secrets or source values.
- [x] Add concurrent success/error isolation tests for one shared client.
- [x] Add `trusted-local` and `shared-hardened` Trino deployment profiles.
- [x] Fail closed when shared-hardened has no finite cumulative scan ceiling.
- [x] Show the effective Trino profile and scan ceiling in required `doctor`
  capability status.
- [x] Document profile names, defaults, units, and startup failure behavior.

## Repository-wide security review follow-ups

- [x] Replace all categorical values in external advisor requests with
  field-scoped synthetic labels/ranks or non-reversible summaries; add common
  name/address values that evade current heuristics.
- [x] Suppress exact `min`, `max`, and percentile metrics for sensitive numeric
  Trino columns; verify `profile_table_safe`, legacy conversion, and generated
  planning artifacts do not contain singleton source values.
- [x] Validate advisor-proposed DatasetSpec constraints semantically before
  persistence; reject string constants, unknown references, and sensitive
  targets, then re-run privacy and type checks after constraint solving.
- [x] Replace formula/validation diagnostics that reflect expressions, ASTs,
  expected/actual values, or nested exceptions with fixed local reasons.
- [x] Apply the same bounded pre-parse raw-frame and final-response transport
  policy to generator MCP, with a fresh invocation budget and tests for
  oversized frames, IDs, errors, and nested responses.
- [x] Enforce JSON node/container/depth/scalar limits before full object
  materialization and convert parser recursion/resource failures to bounded
  input errors.
- [x] Validate public artifact names as safe single components.
- [ ] Reject symlink targets in overwrite-capable CLI artifact paths.
- [x] Neutralize or reject spreadsheet formula markers at the CSV export
  boundary and test advisor, semantic-provider, and categorical inputs.

## Independent security review follow-ups

- [x] PR #331 suppresses provider exception text from normal formatted
  tracebacks for provider-call and structured-validation failures.
- [x] PR #332 reserves placeholder-shaped baseline literals so generated
  placeholders do not collide with them.
- [x] PR #333 replaces raw incomplete-response status text with a fixed local
  message.
- [x] PR #334 detaches handled SDK/provider/validation exceptions from both
  `__cause__` and `__context__`.
- [x] PR #335 replaces positional profile-to-baseline rare-category matching with
  field-scoped value matching that is independent of category order.
- [x] Add a deterministic postcondition proving that no original rare value
  remains in the sanitized profile, baseline, or serialized `AdvisorRequest`.
- [x] Make persisted-review verification distinguish generated placeholders
  from ordinary placeholder-shaped literals without positional restoration.
- [x] Drop handled SDK/provider exceptions from both `__cause__` and
  `__context__` for client initialization, provider calls, and structured
  validation.
- [x] Catch every ordinary SDK constructor `Exception`, including exceptions
  outside `OpenAIError`, then raise the fixed local `ValueError` only after
  leaving the active handler so no raw text or exception chain survives.
- [x] Replace dynamic Python exception class names in provider-call errors with
  one fixed allowlisted local message.
- [x] Replace raw `response.status` reflection with a fixed bounded local error
  reason and keep provider-controlled status text out of errors and metadata.
- [x] Add synthetic regressions for reordered baselines, placeholder literals,
  handled constructor/provider failures, invalid output, incomplete status,
  formatted tracebacks, and direct `__cause__`/`__context__` inspection.
- [x] Add regressions for an ordinary non-`OpenAIError` constructor exception
  and a provider exception with a marker in its Python class name; assert exact
  fixed messages and empty cause/context chains.
- [x] Rerun the independent review for the exact PR #335 merge tree and record
  scan `0ba29f2e-47fe-4baa-af7a-4b4a64cbe348`; it closes RC6-S1 and identifies
  the remaining RC6-S2/S3 work.
- [ ] Rerun independent review on the next fixed immutable commit and close or
  explicitly approve every finding in `security-review-evidence.md`.

## Supply-chain and release gate hardening

- [x] Run change classification from trusted base code or force heavy checks
  whenever classifier, workflow, dependency, build, release, or configuration
  paths change.
- [x] Require a signed release tag and verify it resolves to the
  reviewed RC6 commit digest before building, attesting, signing, or
  publishing any artifact or container; deployed tag immutability remains
  part of the external ruleset evidence below.
- [ ] Add a machine-readable RC acceptance manifest containing reviewed commit,
  closed findings, approvals, artifact digests, and gate results; make release
  workflows fail closed when it is missing, stale, or incomplete.
- [ ] Install every public profile and upgrade from public `0.12.0` with
  hash-pinned dependency and package requirements matching the verified
  release wheel, not only a version constraint.

## Additional RC6 findings previously treated as follow-up questions

- [x] Bound the active MCP request registry and Trino concurrency globally;
  release request state on cancellation, disconnect, timeout, and teardown,
  and return a fixed bounded error when the cap is exhausted.
- [x] Redact Trino driver, catalog, and schema enumeration failures at the
  MCP boundary; define and test whether catalog/schema discovery is allowed to
  reveal backend metadata before allowlist filtering.
- [x] Give the explicit opt-in `run_safe_select` surface a separate, explicit
  row-privacy contract: either allowlist non-sensitive columns or synthesize/
  mask all returned strings, with tests for names, addresses, and heuristic
  false negatives.
- [x] Make semantic-provider execution bounded and reproducible: enforce a
  timeout/cancellation boundary, require a deterministic replay or output
  fingerprint for an explicit seed, restrict names/addresses to a synthetic
  namespace, and run post-generation privacy/type checks.
- [x] Harden every filesystem publication and overwrite path against symlink
  and TOCTOU races using one centralized path policy, no-follow descriptor or
  inode validation, and revalidation before publication and cleanup.
- [x] Define single-entity publication completion/read-validation semantics,
  and require explicit approval before replacing sibling artifacts in a
  bundle; test interrupted publication and collision cases.
- [x] Escape or otherwise bound untrusted metadata, paths, and error text in
  CLI and log output so control characters cannot forge terminal or log lines.
- [ ] Record external branch/tag ruleset, required-check, and PyPI Trusted
  Publisher evidence in the RC6 acceptance record; static workflow checks are
  not sufficient proof of the deployed release policy.

## Release and review gates

- [x] Bump active metadata, version module, lockfile, README, installation
  docs, changelog, release docs, and roadmap to `1.0.0rc6`.
- [x] Add this RC6 OpenSpec and a separate acceptance checklist.
- [ ] Record reviewer identity or stable pseudonym, reviewed commit/date,
  files and scope, findings/disposition, and signature or approval URL.
- [ ] Build the exact RC6 wheel and sdist and publish checksums, SBOM,
  provenance, attestations, and signatures.
- [ ] Verify public base, parquet, mcp, trino, mcp+trino, openai, all, and
  container profiles, including `--version`, `demo`, `doctor`, and upgrade
  from `0.12.0`.
- [ ] Run release, security, documentation, lint, typing, compile, and full
  test gates against the immutable RC6 commit.
- [ ] Promote stable only from the accepted RC6 source tree.
