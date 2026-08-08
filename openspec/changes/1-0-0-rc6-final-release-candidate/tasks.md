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
