# ADR-0003: Enforce policy below CLI, MCP and provider adapters

- Status: Accepted — retrospective baseline.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Multiple entry points need the same guarantees. Policy enforced only by argparse or an MCP decorator is bypassable through direct Python calls.

## Decision

Use typed Pydantic/dataclass boundaries on Python 3.11+. Keep deterministic generation/validation and reusable policy independent of filesystem, database, provider and transport composition. Pass seeds, limits and dependencies explicitly.

CLI/MCP translate requests and present outcomes; services/core enforce safety. Preserve documented compatibility wrappers during extraction, without reverse imports from extracted services to wrappers. Dependency direction and unique policy ownership have executable architecture tests.

## Alternatives and consequences

Duplicating rules in each interface causes drift; a wholesale rewrite unnecessarily breaks supported imports. Incremental extraction with direct-service tests retains behavior while moving ownership. Internal module names do not become public API because they appear in architecture docs.

## Evidence

Sources: [application boundaries](../reference/application-boundaries.md), [contribution boundary rules](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/CONTRIBUTING.md), [AGENTS](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/AGENTS.md).
Executable anchor: [architecture gate](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_application_architecture.py).

## Revisit when

Revisit ownership when a new interface needs policy currently trapped in an adapter, not merely because a module has grown.

