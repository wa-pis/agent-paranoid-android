# 1.3.2rc2 Published Release Evidence

The protected SSH-signed tag `v1.3.2rc2` identifies exact main commit
`1b32c24fce2ba13916ee5e2a800de8aaa5176c8a`. RC2 completed public acceptance and is the accepted
source tree for version- and documentation-only stable `1.3.2` promotion.

## Scope And Independent Review

RC2 supersedes [accepted RC1](release-evidence-1.3.2rc1.md) because stable
preparation exposed malformed property-test input: the reserved keyword `AS`
was generated as an unquoted SQL catalog. SQL parsing correctly failed before
the expected allowlist rejection. RC2 prefixes unquoted names with `outside_`,
retains arbitrary quoted identifiers, preserves the strict `AllowlistError`
assertion, and adds four explicit examples. No production code, dependency,
schema, fixture, workflow or container behavior changes from RC1.

[PR #494](https://github.com/wa-pis/agent-paranoid-android/pull/494) merged with
all checks green. [Independent exact-commit AI-assisted approval](https://github.com/wa-pis/agent-paranoid-android/issues/495)
by OpenCode / Nemotron 3 Ultra Free reviewed the public source and final gate
metadata. This is not human approval. No local logs or private project material
were sent in that review. The exact-main local release gate passed 1289 tests
with 10 live-service skips and 90.35% coverage; strict documentation passed.

| Gate | Evidence | Result |
| --- | --- | --- |
| Release artifact preflight | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34058122420) | Passed |
| OpenSSF Scorecard | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34058112212) | Passed |
| Security | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34058112213) | Passed |
| Documentation | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34058112197) | Passed |
| Containers | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34058112253) | Passed |
| CI | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34058112195) | Passed |
| Release / GitHub artifacts | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34058465760) | Passed |
| Signed multi-platform containers | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34058465841) | Passed |
| PyPI Trusted Publishing | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34058624583) | Passed |
| Verify Published Release | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34058767753) | Passed |

## Published Artifacts

The [GitHub prerelease](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.3.2rc2)
and [PyPI release](https://pypi.org/project/agent-paranoid-android/1.3.2rc2/)
were published on 2026-09-06 UTC. The signed manifest binds exact source,
independent approval, successful gates, historical finding dispositions and
Ubuntu package hashes. Signature, identity and acceptance checks passed before
push; publication rebuilt matching distributions.

| Artifact | SHA-256 |
| --- | --- |
| `SHA256SUMS` | `3d77397caebe703b3611e450f3467adbbc666d681160cb403e67e7094e6f83cd` |
| `agent-paranoid-android-1.3.2rc2.sigstore.json` | `7611a63bc9c0d83b71d276a09d66d7c3827ec78d17ceffcbdbbc57780802678c` |
| `agent_paranoid_android-1.3.2rc2-py3-none-any.whl` | `4e7c4683fc2a33ffadd1306885d2d49243abe88ac2521d615cd8984660ccc4f2` |
| `agent_paranoid_android-1.3.2rc2.tar.gz` | `121bb7059abf3d9b1e00e0a7fd7ba7ae87c2b65523fa65dfd8d8d9554dae58d7` |
| `sbom.cdx.json` | `f0ac689bde88ff1298b67f3e56a3adb9906665279da70ff8a347bae9ce6f2bc7` |

## Signed Containers

| Image | Multi-platform digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.3.2rc2` | `sha256:d9bcab8291c404b6141250e90269ae20ac5c696ef37669c114eb1b22a1b37bd2` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.3.2rc2` | `sha256:40383086841960549338a21495b8b4ca1c41701dd1f7fc1284a92222eea4595f` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.3.2rc2` | `sha256:1aecfb487d0ea6e6f3d43e227b2b0db27b64a24d7f69906d73181c62772c3c77` |

Public verification checked Python checksums, portable Sigstore and GitHub
attestations, PyPI hash equality, public documentation, synthetic installed-wheel
workflows, image SBOM/provenance, Cosign signatures and hardened health checks.
Images cover linux/amd64 and linux/arm64; clean public installs passed for base,
parquet, mcp, trino, mcp-trino, openai and all. No production data or live
provider credentials were used.
