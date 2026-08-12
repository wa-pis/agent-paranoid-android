# 1.1.0rc2 Partial Release Evidence

Status: **container artifacts published; Python release failed closed**

## Release Identity

The protected signed tag `v1.1.0rc2` resolves to accepted commit
`9ff776b8fc59ed8037f7dc5aa23d124a61eb6a90`. Independent OpenCode review
approved that exact commit in
[issue #413](https://github.com/wa-pis/agent-paranoid-android/issues/413#issuecomment-5265910932).

The exact-commit [CI](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31589609575),
[Containers](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31589609588),
[Documentation](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31589609556),
and [Security](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31589609565)
gates passed.

## Python Publication

The tag-triggered
[Release workflow](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31590880376)
passed source identity, signature, acceptance-manifest, version, and full
release-gate checks. It then failed before attestation, GitHub Release, or PyPI
publication because the protected manifest carried a macOS-derived sdist
digest while the release runner built on Linux.

The wheel was reproducible across macOS and Linux:

```text
agent_paranoid_android-1.1.0rc2-py3-none-any.whl
03cc827803423ddca2bd2364a20c19ddcf50fdd489ec6b62ba8cdc3c6e527da1
```

The sdist payload was valid on both systems but its compressed bytes differed:

```text
macOS: bc6b6cf63191af7af9a5ef13a10418693961a234dd6eeb060772d835da8c5e4f
Linux: 457046a16f9bc0f13c5229162ecb6dc4effc1b785dc4052e8a36cee5bc3e3b34
```

The immutable tag rules correctly prevented replacing the signed manifest.
There is no `1.1.0rc2` GitHub Release or PyPI distribution.

## Container Publication

The independent
[container workflow](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31590880317)
published and keylessly signed the accepted source as multi-platform images:

```text
ghcr.io/wa-pis/agent-paranoid-android-cli:1.1.0rc2
sha256:ce30f754198d06435a8f951cc25762f04de7026c28dcb9a03e9b02f5cbd9f89a

ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.1.0rc2
sha256:f5841c0a1256bc78beaa34efb0f382cae362eb9815d90a35895554d66dd08327

ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.1.0rc2
sha256:c2caf17a9865eae3971faabb25d3c35625100d242efbbdb0253cdc43699dd2fb
```

Stable `1.1.0` promotes the same accepted runtime through the allowed
version- and documentation-only path. Stable artifact digests are derived on
Linux before its protected tag is created.
