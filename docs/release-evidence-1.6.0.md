# 1.6.0 Stable Release Evidence

GitHub, PyPI and all three signed container targets are published. Public
verification passed on its first attempt: all 12 jobs succeeded.

## Source and acceptance

The SSH-signed tag `v1.6.0` targets exact main
`258c035c22408becf17ab090635710a50dda8ccc`, merged through
[PR #626](https://github.com/wa-pis/agent-paranoid-android/pull/626).
Its tag object is `54a49885f211eb03ec0c2aa111797702524ea7da`.
Independent technical AI review approved this exact commit with no open findings;
report SHA-256 `f3a4c645158efad686ed4e1f615592b4d0060f0e6cf1bf1a0eeae6d452a14a7d`.
The promotion retains the accepted RC5 runtime; the sole installed production
payload change is version.py. Dependencies, schemas, fixtures, workflows and
behavioral/safety assertions remain unchanged. The archival overlay changes only
documentation context; its executable tail remains byte-identical.

The full local gate passed 4197 tests with 23 classified skips and 91.49%
coverage. Strict documentation and all 30 strict OpenSpec items passed.
All four actual main workflows passed: [CI](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38967722787),
[Containers](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38967722649),
[Documentation](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38967722775),
[Security](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38967722655).
CI includes actual disposable PostgreSQL 4/4, Trino 6/6, minimum MCP 1.28.1
transport 65/65 and Python 3.11–3.14. Container workloads cover all three targets
on AMD64 and emulated ARM64.

## Installed interface and personal acceptance

Both MCP 1.30.0 and 2.2.0 environments used the final Ubuntu wheel. Each passed
600 logical source/output/mode/interface cells with two seeded repeats and
reaped MCP processes; 1080 grouped tracked executions (1001 unique cases), zero
final skips or failures; and 22 external CLI scenarios. Separate transformation
subsets passed 192 selected tests each, twelve fictional supplied-fixture routes
and real-stdio common/configured lifecycle cases. An initially over-restricted
external PATH caused 15 doctor failures per environment; original reports remain
unchanged and separate PATH-only completion runs passed. No product or installed
dependency was changed to repair the test environment.

Actual personal controlling-terminal approval completed the common direct/fallback
and configured owned-capture fictional cases, followed by real-stdio validate and
execute, source cleanup, no reconnect and normal process reaping. The result is
bound to this final source and wheel; result SHA-256
`23c543c70386f41cf961c3bb16f35014d1be07793b4e437a2bf7acfa594645c8`.
This is personal preservation consent for those exact fictional plans, not a
blanket authorization. No agent issued that consent. The earlier actual Codex
specification acceptance retains its RC5 source, version and observation limits;
no fresh stable Codex UI or separate UI-prompt observation is claimed.

Fresh private CSV capacity passed 300000 rows × 50 columns, complete readback,
source integrity and cleanup: 90150450 output bytes, 144.136 seconds measured
by the script's shared monotonic clock under explicit 512 MiB/1800-second
cooperative budgets. The observed UTC interval was 2060.931 seconds; no hard
wall-clock or peak-RSS containment is claimed. Historical twelve 1M × 100 route
measurements retain their actual historical artifacts; they are not fresh stable
public/wire/live-database capacity results.

## Artifact identity

A fresh [Ubuntu no-publish preflight](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38970552654)
and independent re-download/supply-chain audit established these hashes before
signing. All 157 package payloads match exact source and installed environments.

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.6.0-py3-none-any.whl` | `7c2c9b9399112cbfaa08dd3164f0f5b040396ebaa606a9ba42734161d7029ef6` |
| `agent_paranoid_android-1.6.0.tar.gz` | `1b02f0dcd585d2d985003769faf1df04e5d44538b5d693ac5a5eea6f0e02d1e7` |

## Publication and public verification

[Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/39017294518),
[PyPI](https://github.com/wa-pis/agent-paranoid-android/actions/runs/39017970928) and
[Containers](https://github.com/wa-pis/agent-paranoid-android/actions/runs/39017294527)
succeeded. The stable [GitHub release](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.6.0)
was published on 2026-10-17 at 08:35:53 UTC. Both public GitHub and actual PyPI
downloads were independently rehashed against the signed manifest. Both portable
Sigstore attestations verified with the exact release workflow and tag identity.

[Verify Published Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/39018919261)
passed on attempt 1: the resolve job, Python-package/documentation job, all seven
public installation profiles and all three container jobs. Checks include
installation/upgrade, doctor, fictional synthetic and agent approval/audit flows,
published documentation, image provenance/SBOM, keyless signatures and hardened
runtime workloads. Automated approval fixtures do not supply personal consent.

| Image | Immutable multi-platform manifest digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.6.0` | `sha256:9fd052485b86982faca5d201d5cca0c83dffeb12f3caa613fbcbc7759c9f5978` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.6.0` | `sha256:2f160705fcba990966a7cd7c2eef0eae5701a4894cc36c6d910ec5d9d68eaa8a` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.6.0` | `sha256:8e0fb20f9b1b0ce5648d444699eaa723310236ecb9aa620fcb5dc223e5870843` |

All three keyless signatures bind to
`https://github.com/wa-pis/agent-paranoid-android/.github/workflows/containers.yml@refs/tags/v1.6.0`.
The [value-free case ledger](release-ledger-1.6.0.json) records actual finite
case IDs, environment versions and report hashes.


Finite option coverage does not mean every possible formula/value or all option
triples. Aggregate handoffs in the 600-cell matrix are distinct from disposable
live acquisition; injected transformation captures are not live database tests.
Provider adapters remain experimental and no live provider call is claimed.
Prior RC evidence and published tags remain immutable. This later evidence does
not relabel exact-release runtime checks as executions on its own docs commit.
