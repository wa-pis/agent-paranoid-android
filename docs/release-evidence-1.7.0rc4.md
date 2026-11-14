# 1.7.0rc4 release evidence

The signed tag targets `ab511904a8a95319fb25a0728deff1afdf347187`.
[GitHub Release](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.7.0rc4),
[PyPI](https://pypi.org/project/agent-paranoid-android/1.7.0rc4/) and
[three signed GHCR images](https://github.com/wa-pis/agent-paranoid-android/actions/runs/43638000072)
passed [public verification](https://github.com/wa-pis/agent-paranoid-android/actions/runs/43639033000).

The [Ubuntu preflight](https://github.com/wa-pis/agent-paranoid-android/actions/runs/43600453183)
produced the digests recorded in the signed tag. CI, Containers, Documentation
and Security passed on that exact commit. Independent technical review found
no blockers (200 focused tests passed). The full local gate passed (4,926
tests, 25 skips, 91.90% coverage), including a separate strict docs build.

The release owner reported that the fictional MCP run generated 12 customers
and 12 orders and the relationship check passed. This is owner-reported
acceptance; the local artifacts were not independently observed. No permission
to preserve source data is granted.
