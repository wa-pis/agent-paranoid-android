# 1.7.0rc1 Release Evidence

GitHub, PyPI and all three signed container targets are published. All 12
public acceptance jobs passed on attempt 1. Stable 1.6.0 remains recommended.

## Source and review

The SSH-signed tag `v1.7.0rc1` identifies exact main
`64b7c8c3bbb0174fd7e159c4dfb42312045a1716`, merged through
[PR #655](https://github.com/wa-pis/agent-paranoid-android/pull/655).
Tag object: `5e52a2fa822cb521ea9dfdbd14a4d859ff939912`.
The signed acceptance manifest binds this source, historical RC6 finding
closures, fresh independent technical AI approval, four exact-main gates and
the Ubuntu artifact hashes. Approval is technical AI review, not human consent.

Completed Codex Security scan `d788e148-3b39-4f88-a99c-3fefda330bec` covered all
52 authoritative changed source files in stable 1.6.0 through `f49e4e88`, with
supporting tests, templates, prompts, packaging and dependencies. It reported
zero findings, with no deferred source coverage. Report SHA-256:
`39c5fdd86ef5240c83211e9d731767b1b2ef9b2d265c675f2cd6a8a7d23399e6`.
That sealed scan retains its original source identity. Classifier, audit-only
filelock and rejected-relationship corrections received separate supplemental
review. Three scoped reviewers then accepted exact main and independently
confirmed final tree `b36ea90a228e11b4fa5fed7c8db989a5841abf6b`.
Exact-main receipt SHA-256:
`bae5b6e8da3ffd17c25cccdfb1bcad2126c4be02d07f56e52f745cdadf6b186c`.
The receipt and final acceptance are recorded in PR #655.

## Exact-source gates and artifacts

All four exact-main workflows passed:
[CI](https://github.com/wa-pis/agent-paranoid-android/actions/runs/40171680946),
[Containers](https://github.com/wa-pis/agent-paranoid-android/actions/runs/40171680923),
[Documentation](https://github.com/wa-pis/agent-paranoid-android/actions/runs/40171680909),
[Security](https://github.com/wa-pis/agent-paranoid-android/actions/runs/40171680920).
CI includes Python 3.11–3.14, installed-wheel compatibility and minimum dependency
profiles, including OpenAI and MCP. These are fresh results on the tagged source.

The [Ubuntu preflight](https://github.com/wa-pis/agent-paranoid-android/actions/runs/40171699799)
passed the complete locked release gate: 4679 tests, 24 classified skips,
92.04% coverage, lint, types, licenses, budgets, schema freshness and fictional
quickstart. The isolated installed wheel passed. Both artifacts were downloaded
and independently hashed before signing; 173 wheel source payloads matched the
reviewed checkout. The tag-triggered release repeated the gate and matched both
Ubuntu hashes before publication.

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.7.0rc1-py3-none-any.whl` | `4aaf9d7914b97e9b02837cedd76339475d083d34fc0b008087b7917fdf7ddc6a` |
| `agent_paranoid_android-1.7.0rc1.tar.gz` | `b9ecbe4262161191936e710010ba66fe4231d7efbdd40b6b0c2ab5a611584cf7` |

## Publication

[Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/40172735815)
and [PyPI](https://github.com/wa-pis/agent-paranoid-android/actions/runs/40173484474)
succeeded. The [GitHub prerelease](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.7.0rc1)
was published on 2026-10-25 at 07:37:33 UTC. Actual GitHub and PyPI downloads
were independently rehashed against the signed manifest. Portable Sigstore attestations for both downloaded distributions verified
with the exact release workflow and tag.

[Containers](https://github.com/wa-pis/agent-paranoid-android/actions/runs/40172735818)
succeeded for CLI, generator MCP and Trino MCP, including AMD64/ARM64 checks,
provenance/SBOM and keyless signatures. Signature identity:
`https://github.com/wa-pis/agent-paranoid-android/.github/workflows/containers.yml@refs/tags/v1.7.0rc1`.

| Image | Immutable multi-platform manifest digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.7.0rc1` | `sha256:e5546e366cd0a95d30942b9608f59b87688a88d4f084af22d4786e0f4e0fed9b` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.7.0rc1` | `sha256:73931b2a8bcd3e63ae73a4b2a685277c68d193a55cfa3aef3ce50631272d212a` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.7.0rc1` | `sha256:0f4be39f8654285d897fae27c98872f94e7b8b564451c431848df197a869a672` |

[Verify Published Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/40173739663)
passed all 12 jobs: release identity, package/documentation, seven installation
profiles and three container targets. Checks include actual public downloads,
installation/upgrade, doctor, fictional synthetic/agent flows, portable
provenance, SBOM, keyless signatures and hardened container workloads.

## Installed feedback and documented examples

A separate Python 3.11.2 environment installed the exact Ubuntu wheel with all
extras, without importing application code from the checkout. All 600 logical
source/output/mode/interface cells passed with two seeded repeats, logical
readback, validation and normal MCP process reaping. The resolved environment
used MCP 2.3.0, PyArrow 26.0.0 and Pydantic 2.14.1; locked and minimum profiles
retain their separate CI results. Five documented fictional examples and 260
focused feedback regressions passed against the installed package.
The [value-free ledger](release-ledger-1.7.0rc1.json) records each finite case,
its logical/validation hashes, environment and runner/fixture identities.

The first matrix attempt stopped with zero executed cells because the isolated
environment lacked the fixture's shared test helper. Copying that exact test
helper into the environment allowed the complete replay; the product was not
changed. Original failed evidence is retained separately from the successful run.
These are installed-artifact checks, not additional live database, provider,
source-preservation, controlling-TTY or million-row capacity acceptance.
Historical personal approvals and scale results retain their original 1.6.0 or
older artifacts; they do not become 1.7.0 executions.

## Documentation and scope limits

The [candidate guide](https://wa-pis.github.io/agent-paranoid-android/versions/1.7.0rc1/)
and `next` alias were publicly checked with package commit
`64b7c8c3bbb0174fd7e159c4dfb42312045a1716`. PDF, standalone HTML, Markdown ZIP
and offline-site ZIP matched the download manifest. Stable root and `stable`
alias retained package 1.6.0 and their prior documentation identity. Later guide
revisions bind their own documentation commit while retaining the signed package
commit. The stable catalog is not advanced for this candidate.

Historical Trino application settings and external profile provenance remain
unknown. Source-row EAV pivot/unpivot remains outside this synthetic modeling
slice and requires its own authorized transformation change. Synthetic checks
supply no dataset permission or human preservation consent. SQL-result fixtures
are not live database acquisition; native decoder peak RSS and every possible
input/option combination are not established by finite acceptance.

Security-workbench measured usage for the completed review at sealing was
10,995,189 total tokens across five threads (10,960,046 input, including
10,530,560 cached; 35,143 output). This is measured context-inclusive usage,
not an estimate of source-only review cost.


## Original feedback follow-up — 2026-10-25

A separate [installed baseline/candidate replay](feedback-acceptance-1.7.0rc1.md)
binds findings 1–26 and section E to verified public wheels, six original
diagnostic scripts and 782 maintained fictional assertions. It retains initial
harness failures and unverified private/live cases. This documentation follow-up
does not modify the accepted package source, tag or release artifacts.
