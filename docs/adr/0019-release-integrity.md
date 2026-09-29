# ADR-0019: Release immutable reviewed commits and verify public artifacts

- Status: Accepted — retrospective release contract; 1.6 authorization is RC-only.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

A green working tree or merged PR does not prove that downloaded packages/images match the reviewed candidate.

## Decision

Bind release approval, closed findings, exact-commit gates and artifact digests in the signed annotated-tag acceptance manifest. Use the no-publish Ubuntu preflight for matching wheel/sdist hashes. Tags are immutable; corrections use a new candidate number.

Publish via the existing protected GitHub/PyPI OIDC workflows and signed OCI digests. Verify public hashes, attestations, installed-wheel workflows, documentation and images after publication. A stable promotion permits only the documented version/documentation diff; runtime/security/dependency changes require renewed candidate acceptance.

For this 1.6 effort only 1.6.0rc1 is authorized. Independent AI review is explicitly labelled AI, exact-SHA-bound and not a substitute for GitHub-required approvals. It is not required for every ordinary commit/PR; safety-policy review remains separate.

## Alternatives and consequences

Retagging, rebuilding unverified distributions, fabricated approvals or bypassing protection break the evidence chain. Local tests and publication success alone do not establish public acceptance. RC authorization is not stable-release authorization.

## Evidence

Sources: [release process](../release.md), [supply-chain specification](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/release-supply-chain/spec.md), [contribution signing](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/CONTRIBUTING.md), owner instructions recorded in the current project conversation.
Executable anchors: [release identity](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_release_identity.py), [acceptance manifest](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_release_acceptance.py), [artifact tests](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_release_artifacts.py).

## Revisit when

Changed executable scope invalidates approval for that scope; repeat applicable review/gates on the actual candidate, never reuse an unrelated SHA's approval.

