# 1.5.0rc1 Published Release Evidence

The protected SSH-signed tag `v1.5.0rc1` identifies exact commit
`f303a3ad054ebf2fd1dba666e7fb9294132f13d3`. It includes CSV generation
corrections, MCP 2 and OpenAI 3 compatibility, the corrected MCP 1.28.1 minimum,
and container hardening. The candidate completed public acceptance before
stable promotion.

## Independent Review

[Exact-commit AI approval](https://github.com/wa-pis/agent-paranoid-android/issues/509)
was provided by the independent Codex reviewer APA-Release-Reviewer (Pauli).
This is not human approval; the exact model version was not independently
verified. OpenCode/Nemotron returned a provider access error, so no review from
that provider is claimed.

The initial review blocked publication on numeric identifier disclosure and
short-string diversity collapse. [PR #508](https://github.com/wa-pis/agent-paranoid-android/pull/508)
fixed both before any RC tag was created. A fresh patch reviewer found related
float-rounding/exponent bypasses, also corrected before approval. The final
reviewer independently reproduced closure, checked tree identity, queried
exact-commit gates and rehashed downloaded Ubuntu distributions.

Local final-source release gate: 1362 passed, 10 live-service skips, 90.59%
coverage. Lint, types, licenses, safety boundaries, resource budgets, schema,
quickstart and strict documentation checks passed. The independent reviewer
ran focused reproductions, not the entire release suite.

## Gates And Publication

| Gate | Evidence | Result |
| --- | --- | --- |
| CI | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/35787131865) | Passed |
| Security | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/35787131805) | Passed |
| Documentation | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/35787131887) | Passed |
| Containers | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/35787131959) | Passed |
| Ubuntu preflight | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/35787185681) | Passed |
| GitHub Release | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/35787842014) | Passed on attempt 2 |
| Signed containers | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/35787841879) | Passed |
| PyPI Trusted Publishing | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/35788491873) | Passed |
| Public acceptance | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/35788672858) | Passed |

The first GitHub Release attempt stopped before package publication when
GitHub's OIDC service returned `InternalError: error retrieving identity token`
during SBOM attestation. Only failed jobs were rerun. The tag, source,
dependencies and reviewed artifact hashes did not change; no checks were
disabled.

## Public Artifacts

The [GitHub prerelease](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.5.0rc1)
and [PyPI candidate](https://pypi.org/project/agent-paranoid-android/1.5.0rc1/)
are public. Wheel and sdist hashes match the signed acceptance manifest and
Ubuntu preflight.

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.5.0rc1-py3-none-any.whl` | `0b9f230efba2f804efb9db140c7c3ce58c30c87f3fc90f56f474bd5764f9b062` |
| `agent_paranoid_android-1.5.0rc1.tar.gz` | `03e68cff0264f9a091537b017a45e7b92141ffb29e4bc6ae096cb6935a1de622` |
| `agent-paranoid-android-1.5.0rc1.sigstore.json` | `c2890d8fb264e157b822c323b2c15189cf067dee2ade3c4ad40c710b2f3017aa` |
| `sbom.cdx.json` | `98343a7fd7e121bdb88cafb339b76a25226344832ee973d6685bf40885ce6462` |
| `SHA256SUMS` | `4ab753e1cf71979be47b0d84cf577f9bf5b93859d755e2164c2a2c997d17ffb1` |

| Multi-platform image | Digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.5.0rc1` | `sha256:2917ba7780d9808a935b89ab35f8c88b97f3049c7e4065029387c4484ab0bf01` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.5.0rc1` | `sha256:9ca057b6fe13ec2cfa3affa88a4145c2ac32978a7349f9a3b45bd5a39ce4eacf` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.5.0rc1` | `sha256:14901e4d872184ab60405cd33f6687eaee7abf10d4baa3862cc5833727bff5f9` |

Public verification passed for base, parquet, mcp, trino, mcp-trino, openai and
all installations; README doctor/demo and agent approval/audit workflows;
package hashes, portable Sigstore/GitHub attestations, documentation; and all
three multi-platform containers with SBOM, provenance, signatures and health
checks. No production data or live provider credentials were used.
