# RC6 Acceptance Checklist

This checklist applies to the immutable `1.0.0rc6` tag. Local wheels and
source checkouts are not substitutes for the public-artifact checks.

## Source and review identity

- [ ] RC6 tag points to the reviewed fixed commit.
- [ ] Independent security review records reviewer identity or stable
  pseudonym, commit, UTC date, scope, findings/disposition, and signature or
  approval URL in the [review evidence](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/1-0-0-rc6-final-release-candidate/security-review-evidence.md).
- [ ] RC5 is treated as historical and superseded for stable promotion.

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
- [ ] Upgrade from public `0.12.0` succeeds without changing the README
  commands.

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
