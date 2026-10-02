# ADR-0027: Accept complete workflows using fictional, reproducible evidence

- Status: Accepted — baseline and owner workflow direction.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Many passing helpers can coexist with an unusable installed workflow. Private data absence and proposed integrations can also be mistaken for accepted coverage.

## Decision

Use fictional fixtures and normal product paths. Inspect supplied scripts before isolated baseline/candidate execution; do not monkeypatch product safeguards to manufacture a pass. Missing private data or unavailable integrations remain unverified, not passed.

Tie claims to exact environment/artifact/SHA and distinguish unit, private integration, installed user workflow and public artifact acceptance. Run relevant tests for changed scope and full gates at milestones; do not replay unchanged successes or launch overlapping work. Report complete user-visible outcomes and residual gaps, not helper counts as release readiness.

## Alternatives and consequences

Always running the whole suite wastes time; relying only on unit success misses packaging/interfaces. Future feedback cannot be invented as a requirement. AI review evidence is independent from human GitHub approval and cannot replace it.

## Evidence

Sources: [client acceptance](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/client-acceptance.md), [CSV scale evidence](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/csv-scale-acceptance.md), [release process](../release.md), owner instructions in this conversation.
Executable anchors: [installed package](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_installed_package.py), [client modes](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_client_mode_installed_acceptance.py), [publication acceptance](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_client_publication_acceptance.py).

## Revisit when

Before adding a new release gate, identify the accepted requirement it proves; do not invent stronger guarantees or reduce scope to an intermediate pass.

