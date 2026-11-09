# Change Proposal: CPython 3.15 Support

Archive status — 2026-11-09: implemented, merged and publicly verified in
1.7.0rc3 (capacity first shipped in rc2). See
[RC3 release evidence](../../../../docs/release-evidence-1.7.0rc3.md).
The dated proposal/checkpoint descriptions below retain their original scope;
archival grants no dataset authority and does not turn the explicitly waived
RC3 manual client check into a passed check. Performance measurements retain
their actual results and artifact identities.

## Status

Proposed and implemented on 2026-11-08 at the owner's request.
Implementation evidence is recorded in `progress.md`: CPython 3.11–3.15
blocking CI and CPython 3.15.2 Linux/macOS verification passed. No release
is published by this change. At proposal time the tested range was 3.11–3.14. Official sources verified on 2026-11-08 confirm that
[3.15.0 became stable on 2026-10-09](https://www.python.org/downloads/release/python-3150/)
and [3.15.2 was released on 2026-10-26](https://peps.python.org/pep-0790/).
Available local interpreters and dependency wheels remain to be verified.

## Why

Users should be able to install and run the deterministic core and documented
extras on CPython 3.15 with the same safety and resource guarantees. The open
`requires-python >=3.11` declaration permits installation attempts but is not
evidence that a newer interpreter is tested or supported.

## What Changes

- Audit CPython 3.15 and dependency compatibility, including native wheels.
- Exercise the full suite and isolated installed-wheel checks on CPython 3.15.
- Verify real MCP stdio, spawn workers, resource accounting and recovery.
- Extend runtime/dependency CI matrices and support documentation only when
  their evidence is green; retain CPython 3.11–3.14 and existing required checks.
- Resolve dependency constraints explicitly without silently dropping an extra
  or raising the minimum interpreter for existing users.

## Scope

Standard GIL-enabled CPython on the platforms already covered by the relevant
capability. No new Windows scalable-engine support, alternate interpreter,
free-threaded build, JIT performance promise or default container runtime change.
No source-preserving activation, database access, provider API calls or relaxed
approval/privacy/budget gates. No release or tag is authorized by this proposal.

## Acceptance

Record the exact interpreter/platform/dependency profiles, full-suite and
installed-wheel results, supported-extra coverage and synthetic worker/MCP
evidence. Supported stable 3.15 must pass required CI before promotion. If the
available interpreter is a prerelease, label it experimental and keep its
separate compatibility probe nonblocking until promotion; a green experimental
probe alone must not claim stable support. Existing supported versions remain
green. The verified stable release makes blocking stable-version jobs the
implementation path; an experimental probe is not a substitute. Run normal
release gates before any separately authorized publication.
