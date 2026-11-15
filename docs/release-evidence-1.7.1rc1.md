# 1.7.1rc1 release evidence

The signed tag targets `8c42dc60e68a75ba4af2fe3f48690988004c5d72`.
[GitHub](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.7.1rc1),
[PyPI](https://pypi.org/project/agent-paranoid-android/1.7.1rc1/), and
[three signed images](https://github.com/wa-pis/agent-paranoid-android/actions/runs/43744830218)
passed [public verification](https://github.com/wa-pis/agent-paranoid-android/actions/runs/43746064395).
The verifier was rerun after the PyPI simple index exposed the same signed wheel.

Exact-main CI, Containers, Documentation and Security passed. The
[independent technical AI review](https://github.com/wa-pis/agent-paranoid-android/pull/715)
found no blocker. The local gate passed 4,937 tests with 25 skips. The
installed-wheel matrix passed 600 routes for each of MCP SDK 1 and 2;
database inputs in that matrix were fictional stand-ins. No new manual human
acceptance or historical Trino 401 reproduction is claimed.

The [Ubuntu preflight](https://github.com/wa-pis/agent-paranoid-android/actions/runs/43740552445)
produced these SHA-256 digests:

- Wheel: `66082f989840eb5aea5b6f71840771a6bd29c133d1fc91892ca8499656953748`
- Sdist: `e62d31d917d4be3cb26115157ac5360d8e1dc8c55a1709c085f5b8f90c4d75a6`
