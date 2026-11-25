# 1.8.0rc1 release evidence

The signed `v1.8.0rc1` tag targets
`48538d05ec4d9ab6af3ffa951262703bae66f161` (tree
`b94ff53c8aefe44c92d896fb5d0fb1a313e1df74`); its annotated tag object is
`dda79627a1c83119e6084459917e758c83289969`.
[GitHub](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.8.0rc1),
[PyPI](https://pypi.org/project/agent-paranoid-android/1.8.0rc1/) and all three
signed images passed [artifacts-scope public verification](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45589440125) (13/13 jobs).
Publication ran through [Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45586395326),
[PyPI](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45587932168) and
[Containers](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45586395441).

Exact-source [CI](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45582041915),
[Containers](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45582042108),
[Documentation](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45582042137)
and [Security](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45582041876)
passed. The [Ubuntu preflight](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45582089752)
passed the full release gate: **6,222 passed, 26 skipped, 92.25% coverage**.
The 26 skipped tests were not executed; no live database/provider coverage is inferred.

The [independent technical AI source review](https://github.com/wa-pis/agent-paranoid-android/pull/721#issuecomment-7157932935)
closed 17 dispositions and approved one with explicit limits. The independent
[artifact audit](https://github.com/wa-pis/agent-paranoid-android/releases/download/v1.8.0rc1/independent-artifact-audit-1.8.0rc1.md) approved the same source and Ubuntu
artifacts. AI review is not human approval or dataset authorization; the stated
GitHub-administrator trust boundary and unverified current private PyPI
administrator configuration remain explicit limits.

## Artifacts

Ubuntu preflight and public artifacts agree on SHA-256:

- Wheel: `d98e267225a9fa3e51f032acd4fd5399842fd6818d86d99a73fad9eb43a88621`
- Sdist: `071c155bd2a557a567b38aa53b046411e8d845ed6a3294bef18345315862ffe1`

| Signed image | Published digest |
| --- | --- |
| CLI | `sha256:0d4955067fcba7533692c2fcbd67d01c4d4f5bc61c44c2f0e5039142e4734388` |
| Generator MCP | `sha256:5d438ece500cf2819f9510745d3ead39594f2b16c049147afdea3c596f540193` |
| Trino MCP | `sha256:8ac233068c106030ae3140d84c06edf5150fe49554d343d28f596b84a782324f` |

## Installed acceptance

The accepted Ubuntu wheel passed **600/600 core routes for each of MCP SDK1
and SDK2**, with two seeded runs per route and 200 routes per Python, CLI and
real-stdio MCP interface. Same-seed and cross-interface logical/spec/validation/
business-report checks passed; MCP processes were reaped. Database fixtures
were fictional stand-ins.

Separate installed option selections passed **644 SDK2 tests and 100 base
tests, with zero failures or skips**, including all six deadline and three
native-profile-bounds regressions. The base environment had no Arrow, DuckDB
or MCP. Execution used target Python `-I`, no `PYTHONPATH` and a root-only pytest
path override. Installed payload/provenance checks ran before/after, without a
per-test origin recorder. SDK1 used compatibility-only MCP 1.28.1 and httpx-sse 0.4.3; project
dependencies and lockfile were unchanged.

The bounded [installed acceptance asset](https://github.com/wa-pis/agent-paranoid-android/releases/download/v1.8.0rc1/installed-acceptance-1.8.0rc1.json)
has SHA-256 `8f7c3e243f178b0de68c13c8d31db536d8781686667f861dfa6bd235c6f242d5`.
Core routes and selected options are separate finite scopes, not exhaustive
option combinations or new capacity measurements. No live database/provider
campaign, new manual human acceptance or dataset approval is claimed.

## Documentation and retained boundaries

Candidate guidance belongs at
[`versions/1.8.0rc1/`](https://wa-pis.github.io/agent-paranoid-android/versions/1.8.0rc1/).
Its documentation revision and full-scope public verification remain pending;
artifacts-only verification does not establish live guide acceptance.
Stable 1.7.1, its catalog/default and the separate human-review task remain
unchanged. Historical benchmarks retain their original source identity.
Publication activates no new transformation extension and grants no data access.
