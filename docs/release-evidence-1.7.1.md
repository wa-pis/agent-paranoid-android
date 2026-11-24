# 1.7.1 release evidence

The signed tag targets `8aa5d40af2a9f5f15e6572fd2abafdd805df8c9e`. It promotes the
[publicly accepted 1.7.1rc1 runtime](release-evidence-1.7.1rc1.md) with version
and documentation changes only.

[GitHub Release](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.7.1),
[PyPI](https://pypi.org/project/agent-paranoid-android/1.7.1/),
[PyPI publication run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/43749471856),
and [three signed images](https://github.com/wa-pis/agent-paranoid-android/actions/runs/43748652503).
The [public artifact verifier](https://github.com/wa-pis/agent-paranoid-android/actions/runs/43750169209)
passed before promotion of the stable documentation.

The [independent technical AI review](https://github.com/wa-pis/agent-paranoid-android/pull/716),
four exact-main gates and [Ubuntu preflight](https://github.com/wa-pis/agent-paranoid-android/actions/runs/43747550709)
passed. The installed-wheel matrix passed 600 routes for each of MCP SDK 1 and 2,
with fictional database stand-ins. Historical Trino 401 reproduction was outside
this release.

The signed acceptance manifest records the Ubuntu SHA-256 digests:

- `agent_paranoid_android-1.7.1-py3-none-any.whl`: `ecbc9b315f5d4ecdd8f1863c6f8a8add93ce849725cac3f56b82c5c8a55f68ff`
- `agent_paranoid_android-1.7.1.tar.gz`: `6eb5dc499f678f397d1dc19a803dcfbb0115031c9ba2cb9d1ecb56a1f0896413`
