# ADR-0001: Record decisions separately from specifications and progress

- Status: Accepted — documentation organization requested by the owner on 2026-09-29.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Decisions have accumulated in conversations, OpenSpec changes, design pages and progress notes. A prototype's state or an obsolete plan can be mistaken for a product decision.

## Decision

Use this ADR register for architectural choices, their rationale, alternatives, consequences and authority. Specifications define executable behavior; plans sequence work; progress and release evidence record what actually happened. An ADR is not permission to access data, activate a gated feature or publish a release.

Record an existing decision retrospectively only when a cited contract or explicit owner decision supports it. Mark unsupported choices Proposed or put them in the open-question register. “Accepted” describes the decision, not implementation readiness.

## Alternatives and consequences

Keeping only a progress log loses the rationale and replacement history. Creating one ADR per helper would duplicate the code inventory without stabilizing architecture. Group decisions by lasting boundary.

Change an accepted decision with a new ADR explicitly superseding it; retain the old record and reciprocal links. Editorial corrections and new evidence may update an existing ADR without silently changing its decision. New product/security choices still require the existing owner/review authority.

## Evidence

Owner request in this conversation: “без adr мы постоянно мечемся” and “сделай весь объем adr по проекту”. Existing [change workflow](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/CONTRIBUTING.md) and [public change classification](../reference/stability.md) remain applicable; this register adds no replacement release or approval process.

## Revisit when

Revisit if the register itself duplicates contracts or cannot identify which decision governs a change.

