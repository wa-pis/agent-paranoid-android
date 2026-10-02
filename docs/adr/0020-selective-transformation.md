# ADR-0020: Separate mixed-origin transformation from synthetic generation

- Status: Accepted — owner-approved target; public execution gated.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Users need one-to-one selective replacement/preservation, which cannot truthfully be represented as wholly synthetic generation.

## Decision

Build a separately selected mixed-origin transformation workflow. Retain one-to-one row correspondence and order, explicit per-field actions, independent privacy checks and validation-before-publication. Do not route it through source-free generation by weakening that path.

Private fictional implementation and temporary tests may precede final review. Public CLI/Python/MCP execution and source preservation remain disabled until the matching safety amendments, executable evidence and independent review are complete. A parser, receipt helper, read-only review command or merged prototype does not activate it.

## Alternatives and consequences

Treating transformation as a generator flag would blur authority and manifest claims. Requiring final implementation review before any private test implementation would prevent producing the evidence; development and activation therefore have separate gates.

Mixed-origin output is neither anonymous nor fully synthetic. No real dataset, database or provider access follows from permission to develop the feature.

## Evidence

Sources: [AGENTS gated amendment](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/AGENTS.md), [safety boundary](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/safety-boundary.md), [transformation specification](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/specs/selective-source-transformation/spec.md).
Executable anchors: [execution tests](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_transformation_execute.py), [review CLI tests](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_transformation_cli_review.py).

## Revisit when

Any public activation must demonstrate the whole boundary, not infer permission from passing private helper tests.

