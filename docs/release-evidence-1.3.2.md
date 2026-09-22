# 1.3.2 Published Release Evidence

The protected SSH-signed tag `v1.3.2` resolves to exact stable main commit
`28d1176867d3ba155a420a5dfae0f6944597470d`. Stable promotes publicly accepted `v1.3.2rc2`
(`1b32c24fce2ba13916ee5e2a800de8aaa5176c8a`) with version and documentation
changes only. Application runtime, safety-test scenarios, schemas, fixtures,
dependency graph, workflows and container definitions are unchanged from RC2.

## Review And Release Gates

[Promotion PR #496](https://github.com/wa-pis/agent-paranoid-android/pull/496)
merged with all 41 checks complete and no failures. The exact stable commit
received [independent AI-assisted approval](https://github.com/wa-pis/agent-paranoid-android/issues/497)
from OpenCode / Nemotron 3 Ultra Free. Public GitHub source and evidence were
reviewed; this is not a human-review claim. The reviewer approved every changed
hunk against accepted RC2 and the identical final merge tree.

The local exact-main release gate passed 1289 tests with 10 live-service skips
and 90.35% coverage. Strict documentation validation passed. Ubuntu preflight
provided distribution hashes; downloaded files were rehashed locally. Signature,
source identity and signed-manifest acceptance checks passed before tag push.

| Gate | Evidence | Result |
| --- | --- | --- |
| Release artifact preflight | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34059115677) | Passed |
| OpenSSF Scorecard | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34059102604) | Passed |
| Documentation | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34059102716) | Passed |
| Security | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34059102703) | Passed |
| Containers | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34059102619) | Passed |
| CI | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34059102726) | Passed |
| Release / GitHub artifacts | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34059517336) | Passed |
| Signed multi-platform containers | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34059517290) | Passed |
| PyPI Trusted Publishing | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34059663619) | Passed |
| Verify Published Release | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34059767939) | Passed |

## Public Package Identity

The [GitHub stable release](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.3.2)
and [PyPI release](https://pypi.org/project/agent-paranoid-android/1.3.2/)
were published on 2026-09-06 UTC. GitHub marks this release as neither draft nor
prerelease; package maturity metadata is Production/Stable. The signed tag
manifest binds the exact commit, approval, four required gate URLs, historical
finding dispositions and both Ubuntu distribution hashes.

| Artifact | SHA-256 |
| --- | --- |
| `SHA256SUMS` | `9afe08227facc1f94bf8c5086162123b4205a930c596c0757646d5cd249e6dfc` |
| `agent-paranoid-android-1.3.2.sigstore.json` | `17d30ba7d82c1ad9099a273922367a6bf1d56a7d2faa15df4f2e3386a8098162` |
| `agent_paranoid_android-1.3.2-py3-none-any.whl` | `4d76e4c3983a47b216796a6756122548c3daab8bc79e7e2eb2a589b361a3ea27` |
| `agent_paranoid_android-1.3.2.tar.gz` | `2f3c9c87d37704ff550e84030fcde152e6e07e049ffe8157837744b57f134fa2` |
| `sbom.cdx.json` | `6252d2b602d16136bba56e80673df93b75b9261154e85b4d0e0182311b242db6` |

## Public Container Identity

| Image | Multi-platform digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.3.2` | `sha256:f630fda67811da5452b71405e614a4286e2e5ff958360236b69f25486751b575` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.3.2` | `sha256:cd47f322e82a7d2c6002dafb1f8e232a9fd8c566e2274afaa19383a4e1877940` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.3.2` | `sha256:d740cdfdebe944dfd8ca6d92cda942a3a8cab31dd216983c17932a2eeda72415` |

Public acceptance verified downloaded checksums, portable Sigstore bundles,
GitHub attestations, PyPI hash equality, public documentation, synthetic
installed-wheel workflows, SBOM/provenance, Cosign signatures and hardened
container health checks. Images cover linux/amd64 and linux/arm64. Clean public
installs passed for base, parquet, mcp, trino, mcp-trino, openai and all profiles.
No production data or live provider credentials were used.

## OpenSpec Completion

Generation-contract hardening completed executable semantics, publication and
privacy enforcement, regression/security review and release acceptance. RC1
carried the corrective runtime; RC2 corrected malformed randomized SQL test
input while retaining the runtime. Stable promoted accepted RC2 unchanged.
The completed change is retained in the
[OpenSpec archive](https://github.com/wa-pis/agent-paranoid-android/tree/main/openspec/changes/archive/2026-09-07-generation-contract-hardening).
See the [migration guide](reference/generation-contract-migration.md) before
regenerating fixtures whose formula order, nullable keys or string lengths change.
