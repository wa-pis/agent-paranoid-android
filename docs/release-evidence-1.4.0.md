# 1.4.0 Published Release Evidence

The protected SSH-signed tag `v1.4.0` identifies exact main commit
`5bcaef2cd991e63098de4d1601f8ae2a8207bd14`. This requested minor-version release retains the
publicly accepted `1.3.2` runtime (`28d1176867d3ba155a420a5dfae0f6944597470d`).
Only version and documentation metadata changed; there are no new application
features, API, dependency, schema, fixture, safety-test, workflow or container
changes. The existing version-only exception permits reuse of that accepted
runtime without another RC. New exact-commit acceptance was still required.

## Independent Review And Gates

[PR #499](https://github.com/wa-pis/agent-paranoid-android/pull/499) merged after
required checks passed. Its CodeQL job was rerun after GitHub timed out while
processing the uploaded analysis; the retry and server-side check passed.
[Independent exact-commit AI-assisted approval](https://github.com/wa-pis/agent-paranoid-android/issues/500)
used OpenCode / Nemotron 3 Ultra Free with public GitHub source, workflow and
artifact evidence only. This is not a human-review claim. The complete diff
from accepted `1.3.2` and the identical final merge tree were reviewed.

The exact-main local release gate passed 1289 tests, with 10 live-service skips
and 90.35% coverage. Strict documentation validation passed. Downloaded Ubuntu
preflight package hashes matched local rehashes. Signature, source identity and
signed-manifest artifact checks passed before tag push.

| Gate | Evidence | Result |
| --- | --- | --- |
| Release artifact preflight | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34060878123) | Passed |
| OpenSSF Scorecard | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34060862004) | Passed |
| Documentation | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34060862014) | Passed |
| Security | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34060862108) | Passed |
| Containers | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34060862003) | Passed |
| CI | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34060862065) | Passed |
| Release / GitHub artifacts | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34061172608) | Passed |
| Signed multi-platform containers | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34061172662) | Passed |
| PyPI Trusted Publishing | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34061316527) | Passed |
| Verify Published Release | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34061444182) | Passed on attempt 2 |

## Published Packages

The [GitHub stable release](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.4.0)
and [PyPI release](https://pypi.org/project/agent-paranoid-android/1.4.0/)
were published on 2026-09-06 UTC. GitHub marks the release as neither draft nor
prerelease. The signed manifest binds exact source, independent approval,
required gate URLs, historical finding dispositions and Ubuntu package hashes.

| Artifact | SHA-256 |
| --- | --- |
| `SHA256SUMS` | `1d763eb484ff740f180260bc4e61286626eae1f00a0abf706903b9e9b7376c9c` |
| `agent-paranoid-android-1.4.0.sigstore.json` | `170524c664dae3422059a06a20dd13ec8e1e06dd31b578f2c6a462ba3000eeab` |
| `agent_paranoid_android-1.4.0-py3-none-any.whl` | `6b20e32cbcda8ae78cd976c833587917eee3275cdc5990a2579718778170559c` |
| `agent_paranoid_android-1.4.0.tar.gz` | `a009133585b45ab620bcdb58188a64523c9cbcc137b269a12d41f510098b7ce7` |
| `sbom.cdx.json` | `46926aa1c583128b86b8393e238d59669da661bd96ab17a3a1555480c9ab8fc7` |

## Signed Containers And Public Acceptance

| Image | Multi-platform digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.4.0` | `sha256:e97e2572b9b0a97a5d4ff3b878543593a4890827a06af6fea58a47708f93f2a9` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.4.0` | `sha256:79d86ad6dd56c0eeec8863b4fa2e4c8fe96ca45c7197bcee14d0ff17d9aea8ba` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.4.0` | `sha256:dc0534a258a05c2deae92a4b3abc1b300f4446144926df494fba84c9f2a38455` |

All images cover linux/amd64 and linux/arm64. Public checks verified package
checksums, portable Sigstore and GitHub attestations, PyPI hash equality,
documentation, installed-wheel synthetic workflows, SBOM/provenance, Cosign
signatures and hardened container health checks. Clean installation profiles
base, parquet, mcp, trino, mcp-trino, openai and all passed.

Attempt 1 passed every public check except the Parquet installation: its PyPI
index response did not yet list version `1.4.0`, while other installations had
already succeeded. Only the failed job was rerun; attempt 2 passed without
changing code, dependencies, artifacts or the protected tag. No production data
or live provider credentials were used.
