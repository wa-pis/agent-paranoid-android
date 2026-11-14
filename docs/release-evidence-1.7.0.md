# 1.7.0 release evidence

The signed tag targets `daf3ec87c404ca76b81ca81b3aba635125060240`.
See the [GitHub Release](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.7.0),
[PyPI package](https://pypi.org/project/agent-paranoid-android/1.7.0/), and
[three signed GHCR images](https://github.com/wa-pis/agent-paranoid-android/actions/runs/43643514172).
The [public artifact verification](https://github.com/wa-pis/agent-paranoid-android/actions/runs/43647518211)
passed on the packages and containers for this exact tag before site promotion.

The [Ubuntu preflight](https://github.com/wa-pis/agent-paranoid-android/actions/runs/43642183737)
supplied the signed manifest's wheel and sdist digests. Exact-source CI,
Containers, Security, Documentation, independent review, and the local release
gate (4,926 passed, 25 skipped) passed. The accepted runtime, dependency
resolutions and fixtures match [1.7.0rc4](release-evidence-1.7.0rc4.md).
The manual fictional MCP result is recorded there against that candidate.
