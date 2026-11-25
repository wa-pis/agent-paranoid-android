# 1.8.0 release evidence

Stable 1.8.0 is published and its packages and three signed images are publicly verified.
The signed `v1.8.0` tag targets `b62bc17e49800e17f521cf5ea9f9043f55e0c5b8`
(tree `714035198e99059f9c8d3ea84a0b24167013a76e`); its annotated tag object is
`3251c73e41925a346d1809b9ac61e819b582a2a8`.
[GitHub](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.8.0), [PyPI](https://pypi.org/project/agent-paranoid-android/1.8.0/) and all three
signed images passed [artifacts-scope public verification](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45611255179)
(13/13 jobs).
The [Release workflow](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45608232472) passed and the GitHub stable release is published.
[PyPI](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45609755195) passed. Public GitHub/PyPI distribution hashes and sizes match the accepted Ubuntu artifacts; stable-tag/source/workflow/environment publisher claims were verified.
The [Containers workflow](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45608232495) passed all 11 jobs. Anonymous public registry manifests confirm the listed digests for both `linux/amd64` and `linux/arm64`.
Artifacts-scope verification completed with all 13 jobs passing and no skips.

## Promotion and exact stable-source gates

This is a version/documentation-only promotion of the
[accepted 1.8.0rc1 runtime](release-evidence-1.8.0rc1.md). Runtime behavior,
dependencies, build settings, seeds, privacy boundaries and test scenarios are
unchanged. Candidate acceptance and historical benchmarks retain their original
source/artifact identities; they are not fresh stable execution evidence.

Exact-source [CI](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45603349901), [Containers](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45603349621),
[Documentation](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45603349539) and [Security](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45603350294)
passed. The [Ubuntu preflight](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45603390766)
passed the full release gate: **6,222 passed, 26 skipped,
92.25% coverage**. Skipped tests were not executed;
no live database/provider coverage is inferred.

The [independent technical AI source review](https://github.com/wa-pis/agent-paranoid-android/pull/723) approved the exact stable source.
The [independent artifact audit](https://github.com/wa-pis/agent-paranoid-android/releases/download/v1.8.0/independent-artifact-audit-1.8.0.md) passed for the exact stable source and accepted Ubuntu artifacts.
All 18 source finding dispositions remain recorded: 17 closed and RC6-S20 approved within its stated external-control limits. Current private PyPI administrator settings were not inspected.
AI review is not human approval or dataset authorization.

## Artifacts

Accepted Ubuntu preflight and verified public GitHub/PyPI distributions agree on SHA-256:

- Wheel: `c7a8d059835494cce6e3461c5ee987e0d5eed1e095814850ce82a420540aa06d` (469,364 bytes)
- Sdist: `b352f5fb2c6fbe4c5322dba4764babae291b22bf2e6761d80bc93f9a4461ed9e` (3,091,827 bytes)

| Signed image | Published digest |
| --- | --- |
| CLI | `sha256:b7764a1e989fc23f4037cecc8a4cb4115aa6bef92ea6177a36d6dc822d73a42d` |
| Generator MCP | `sha256:4f33186a1abf7aa8bb805cf782cbc2e533ddaae7d3d4607552b42ae42c76fb5b` |
| Trino MCP | `sha256:d2824d266aba8550551a0dda8bacfa39699df8ae2c946131292101b9b0c6ec70` |

## Installed acceptance

The accepted stable Ubuntu wheel passed **600/600 core routes for MCP SDK1** and
**600/600 for MCP SDK2**, with
two seeded runs per route.
Each SDK covered 200 routes per Python, CLI and real-stdio MCP interface; repeat and cross-interface logical/spec/validation/business-report checks passed, and MCP processes were reaped. Installed payload/origin and dependency checks passed before/after. Each SDK also matched all 600 publicly hash-bound accepted RC routes across six declared logical/specification/validation/business/count fields with zero differences. This is logical parity, not byte identity of version-dependent artifacts. Database fixtures were fictional stand-ins.

Separate installed option selections passed **644 SDK2
tests and 100 base tests**, with
0 failures and 0 skips.
All six captured-deadline/pre-spawn and three native-profile-bounds regressions passed. The base environment had no Arrow, DuckDB or MCP. Execution used target Python `-I`, no `PYTHONPATH` and a root-only pytest path override. Before/after installed package and dist-info payload/provenance checks passed; dependency maps were unchanged. No per-test origin recorder was used.
SDK1 used compatibility-only MCP 1.28.1 and httpx-sse 0.4.3; project dependencies and lockfile were unchanged.

The public bounded [installed acceptance asset](https://github.com/wa-pis/agent-paranoid-android/releases/download/v1.8.0/installed-acceptance-1.8.0.json)
has SHA-256 `864ca216c388d606303c054d28b9762c83402da5dcbf45c9aed2a65eb9c1c9ec`.
The public [artifact audit](https://github.com/wa-pis/agent-paranoid-android/releases/download/v1.8.0/independent-artifact-audit-1.8.0.md) has SHA-256
`c194ff99776137e10034d1190a0b0621cc18090cf944f6c8cdba00e2f35aab75`.
Both assets were downloaded without authentication and matched the reviewed
bytes and hashes.
Core routes and selected options are separate finite scopes, not exhaustive
option combinations or new capacity measurements. No live database/provider
campaign, new manual human acceptance or dataset approval is claimed.

## Documentation and retained boundaries

Stable guidance belongs at
[`versions/1.8.0/`](https://wa-pis.github.io/agent-paranoid-android/versions/1.8.0/).
The documentation revision and full-scope public verification are tracked
separately; artifacts-only verification does not establish live guide acceptance.
Historical documentation, RC evidence and benchmarks keep their original
identities. The separate human-review task remains open. Publication grants no
source access, dataset approval or new transformation activation.
