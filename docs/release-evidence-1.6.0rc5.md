# 1.6.0rc5 Published Release Evidence

GitHub, PyPI and all three container publication workflows succeeded.
Post-publication acceptance passed on the first attempt: all 12 jobs of
`Verify Published Release` succeeded with no failures.

## Source and acceptance bindings

The protected SSH-signed tag `v1.6.0rc5` targets frozen exact main
`890925afdff68e97cafe38a28605d2874c9dad79`, merged through
[PR #623](https://github.com/wa-pis/agent-paranoid-android/pull/623).
The tag object is `1905b2e9b3b53b7233c41ccaa61ff28b48139950`.
The signed acceptance manifest has SHA-256
`022504a5c87e4fd4b181bd5f135f79471fa52cadc3eff98bc4fb8f71fdab025c`.
Independent local checks passed for the tag signature, exact source identity,
manifest and actual Ubuntu preflight artifact hashes. Their audit record has
SHA-256 `a83c701d9531e9305dac7cf5329d14d60677a7d8eb5c9631b05391e39b607c5b`.

The [exact-main candidate checkpoint](acceptance-evidence-1.6.0rc5.md#exact-rc5-candidate-checkpoint)
records the 4197-test gate, 23 classified skips, independent AI source approval,
all four main workflows, fresh Ubuntu preflight and the two installed 600-cell
MCP SDK matrices. The [actual Codex and human specification acceptance](acceptance-evidence-1.6.0rc5.md#actual-codex-and-human-specification-acceptance)
records current-file review and new consent before generation, validation and
the separate artifact audit. Its UI/client-exit observation limits remain in
effect. Dataset consent, AI source review and release authorization are distinct.

## Observed publication

| Publication | Evidence | Result |
| --- | --- | --- |
| GitHub Release | [Release workflow](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38951719133) | Passed; [release](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.6.0rc5) published at 2026-10-16 19:07:52 UTC. |
| PyPI Trusted Publishing | [Publication workflow](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38952634553) | Passed; public distribution hashes independently matched the Ubuntu preflight. |
| Three container targets | [Publication workflow](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38951719128) | All 11 jobs passed; published immutable digests and keyless signature checks are recorded below. |
| Public acceptance | [Verify Published Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38954003435) | First attempt passed: all 12 jobs, no failures. |

The public [PyPI release](https://pypi.org/project/agent-paranoid-android/1.6.0rc5/)
reports these distribution hashes, matching the independently downloaded
[Ubuntu preflight](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38923785970)
artifacts and signed acceptance manifest:

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.6.0rc5-py3-none-any.whl` | `969f969d57c0c87784cf7708d165507d8c3cd34eb41dccccaff43bdd08dea6d1` |
| `agent_paranoid_android-1.6.0rc5.tar.gz` | `d2011e802d64157e9351805e94f97e2202b4c52a7c14511f6b6973b1079d3ae8` |

Successful publication logs identify these immutable multi-platform manifests.
Keyless signature verification passed with the exact signing-workflow identity
`https://github.com/wa-pis/agent-paranoid-android/.github/workflows/containers.yml@refs/tags/v1.6.0rc5`.

| Image | Immutable manifest digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.6.0rc5` | `sha256:9c689636584ff0869e2b833a939c5d4b5079a5e159464965092981b4e2f4ed9d` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.6.0rc5` | `sha256:9b34331eac8f83a356cf89eac856dcbc40a0ef3f9ef623f409ebeac94692fbc5` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.6.0rc5` | `sha256:aec10dffce92a76139eaa54ab972658685bd515fb497cb2b588746bd8a21fdb1` |

## Public acceptance and limits

[Verify Published Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38954003435)
passed the Python-package/documentation job, all seven public installation
profiles and all three container verification jobs. The workflow checked GitHub
distribution checksums and provenance, public PyPI hashes, installation and
upgrade, doctor and fictional synthetic demos, exact-specification agent approval
and audit verification, published documentation, and the signed container
manifests, SBOM/provenance and hardened runtime workloads. Automated agent-approval
checks exercise fictional fixtures; the actual human specification acceptance
remains the separate evidence linked above.

The [coverage limits](acceptance-evidence-1.6.0rc5.md#coverage-limits-and-unresolved-steps)
remain: finite option coverage is not every possible combination, matrix
acquisition handoffs are distinct from live database acquisition, and excluded
legacy combinations are not passes. The separately gated transformation/session
campaign remains open. This ordinary synthetic run grants no preservation
authority. Published RC3 and RC4 stay immutable.

This post-publication documentation does not change the frozen source or tag,
and its later commit does not inherit exact-C runtime execution evidence as its
own.
