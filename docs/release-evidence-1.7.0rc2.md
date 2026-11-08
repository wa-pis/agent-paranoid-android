# 1.7.0rc2 Release Evidence

GitHub, PyPI and all three signed multi-platform container targets are published.
All 12 public acceptance jobs passed on attempt 1. Stable 1.6.0 remains recommended.

## Source and review

The owner authorized the next candidate on 2026-11-08. [PR #689](https://github.com/wa-pis/agent-paranoid-android/pull/689)
merged after all 40 PR checks passed. SSH-signed tag `v1.7.0rc2` targets exact
main `b996da8e4db1435406ac39b5294d234c4a9f9c6c`; tag object
`983ae3e75e77a79a1ccdea4225fb612fde445693`. Its tree is
`520aebf22a9e0a280f26cb8aa2ef30d6ca1471ee`, identical to the reviewed branch.
SHA-256 of the raw signed commit object:
`146e63a8564282e5e9d077c005ff65c42bc2bb8681d1dafaa114b2e47bc6eb28`.
GitHub verifies the merge signature. The release tag's SSH signature was
verified with the repository's allowed signer; its JSON acceptance message
binds source, historical RC6 finding closures, fresh independent technical AI
acceptance, four exact-main gates and Ubuntu artifact hashes.

The read-only independent AI reviewer inspected resource admission, deterministic
distinct-row streams, schema/privacy enforcement, deadlines and worker cleanup,
atomic publication, streamed recovery, calibration/cache and MCP boundaries.
No open release-blocking findings remained. The [exact-main review receipt](https://github.com/wa-pis/agent-paranoid-android/pull/689#issuecomment-6718323122)
is technical AI acceptance, not human consent or GitHub approval. Historical
human client records retain their original version and scope.

## Gates and artifacts

All exact-main workflows passed:
[CI](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42455533808),
[Containers](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42455533823),
[Documentation](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42455533819),
[Security](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42455533795).
The [Ubuntu preflight](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42455554261)
passed 4827 tests with 25 skipped and 91.87% coverage, the full release
gate, and isolated installed-wheel smoke/doctor checks. Local macOS release
gates passed 4826 tests with 26 skips and the same coverage; the Linux-only
spawn regression was explicitly skipped locally and passed in Ubuntu.
Of the 25 Ubuntu skips, 23 runtime skips map directly to source predicates:
10 live-service opt-ins, four isolated composition flags, six prospective-stdio
preservation cases, two inapplicable retained-destination combinations and one
isolated OAuth candidate path. Two collection skips are inferred from missing
MkDocs in the preflight environment; their explicit reasons were not emitted.
This qualifies the earlier PR receipt wording “classified skips”.

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.7.0rc2-py3-none-any.whl` | `320df414ab44d5cedd690a2b9554e77b8dff15e8de07abc08d6784d8468415b1` |
| `agent_paranoid_android-1.7.0rc2.tar.gz` | `b6707616186b808b237cafd2b88daea6b200c3758f0e76d50a2e83bf05dc3984` |

Both the maintainer agent and independent reviewer rehashed the downloaded
archives. The reviewer compared 180 wheel payloads and 1228 sdist checkout
files without extraction; all matched reviewed source, including packaged
prompts/skills. Generated sdist PKG-INFO matched wheel METADATA. See the
[artifact receipt](https://github.com/wa-pis/agent-paranoid-android/pull/689#issuecomment-6718404627).

A separate isolated installation of the exact Ubuntu wheel, with no checkout
imports, passed 49 capacity/identity tests; one Linux-only test was skipped on
macOS. Environment: Python 3.13.14, MCP 2.3.0, PyArrow 26.0.1, Pydantic 2.14.3,
Faker 40.44.0. These tests used only fictional fixtures.

## Resolved pre-merge failures

Initial version-preparation checks detected stale installation pins and pending
publication wording; documentation was corrected without weakening tests.
Container CI then identified CVE-2026-109518 in pinned-base APT 2.6.1; builds
now require Debian-fixed apt/libapt 2.6.2, with acquisition retries disabled
during upgrade and scanning retained. All six architecture/target validations
passed after the correction. [Debian advisory](https://security-tracker.debian.org/tracker/CVE-2026-109518)

Full Ubuntu tests exposed false four-worker memory rejection while macOS
checks passed. Linux getrusage retained the parent's pre-exec memory history.
Bounded current-image VmHWM measurement with conservative fallback corrected
accounting without increasing policy limits. The previously failing tests and
new Linux spawn regression passed across Python 3.11–3.14.

## Publication and public acceptance

[Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42456435569),
[PyPI](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42456940097)
and [Containers](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42456435550)
completed successfully. The [GitHub prerelease](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.7.0rc2)
was published on 2026-11-08 at 06:59:35 UTC. Actual public GitHub and PyPI
wheel/sdist downloads were rehashed against the signed manifest. Both public
GitHub distributions passed portable provenance verification with the exact
release workflow identity and `refs/tags/v1.7.0rc2` source reference.
The tag-triggered build repeated release checks and matched Ubuntu preflight
hashes before attestation and publication.

| Image | Immutable multi-platform manifest digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.7.0rc2` | `sha256:e29616118d0c0d93efa83d7e8841cb8f6c67731b2dd67717fff509749c843867` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.7.0rc2` | `sha256:5281eed067f21e84310a9df7139671e05aec461f1197eb1fd846212d3e121803` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.7.0rc2` | `sha256:58deff882607c541edeba277d7d863321efded3f620688256218346f3d4f18de` |

[Verify Published Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42457481438)
passed all 12 jobs on attempt 1: immutable identity, package/documentation,
seven public installation profiles and three container targets. Checks cover
actual public downloads, installation/upgrade, doctor, fictional synthetic and
agent workflows, portable build provenance, image SBOM/provenance, keyless
signatures and hardened container workloads. Container signature identity is
`https://github.com/wa-pis/agent-paranoid-android/.github/workflows/containers.yml@refs/tags/v1.7.0rc2`.

## Scope and limits

[Capacity guidance](how-to/dataset-capacity.md) describes byte/time ranges,
explicit budgets and the independent-table scalable engine. Relationships,
global rules and unsupported generation modes use the existing bounded path;
the new engine rejects them before generation. Scalable execution requires Linux or macOS; native Windows execution of this
engine is unsupported in this RC. Memory checks are cooperative,
not OS isolation. Timing forecasts cover standalone source-free bundles and
exclude attached-source scans and human review. Benchmark evidence retains its
measured implementation/environment identity rather than becoming a later
release-artifact performance measurement.

No production data, live database/provider execution, source-preserving
transformation activation or new human dataset approval is claimed. Stable
1.6.0 retains the default documentation; candidate guides are isolated under
`versions/1.7.0rc2/`.
