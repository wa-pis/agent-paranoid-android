# Change Proposal: fix-ci-dependency-vulnerabilities

## What Changes

Update only locked audit-tool MessagePack to 1.2.3 and require fixed Bookworm
OpenSSL packages in the shared runtime image. Restore vulnerability gates for
main and the five pending action-update PRs without suppressing findings.

## Why

CI on PR658 (40704469304) flags msgpack1.2.1 / CVE-2026-114613; container
validation (40704469386) flags openssl/libssl3 3.0.20-1~deb12u2 /
CVE-2026-84782. Maintainer advisory fixes MessagePack in1.2.3; Debian fixes
Bookworm in3.0.22-1~deb12u2. Installed vulnerable inventory is established,
not an exploit against this application. The maintainer's earliest affected
MessagePack release is uncertain. No DTLS use was found in project code.

## Scope

Lock-only MessagePack patch; targeted shared-runtime OpenSSL upgrade with
version assertions; existing container contract and scanner/workload checks.
No dependency-wide refresh, ignored CVEs, relaxed scan policy or runtime API
change. Existing signed artifacts/tags stay immutable; this is unreleased
maintenance, not authorization to republish1.7.0rc1 or advance stable.

## Safety and compatibility

MessagePack is dev pip-audit → cachecontrol, not an application dependency.
All three final image targets inherit the same patched runtime. Preserve
read-only DB access, HTTPS certificate verification, non-root hardened images,
source-free generation, local preservation authority and Python3.11–3.14.
No source rows, external databases, providers or new dataset permissions.
