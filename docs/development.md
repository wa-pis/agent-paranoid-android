# Development

Project setup, contribution rules, signed commits, testing expectations, and
pull-request guidance live in
[CONTRIBUTING.md](https://github.com/wa-pis/agent-paranoid-android/blob/main/CONTRIBUTING.md).

For architecture and ownership boundaries, continue with
[Architecture Decision Records](adr/index.md),
[Architecture](agent_design.md) and the
[Application Boundary Baseline](reference/application-boundaries.md).

Use the decision register to distinguish accepted contracts from private
implementation and unresolved choices. Changes to an accepted architectural
decision need an explicit successor record; progress notes are not a substitute
for decision authority. The [open-question register](adr/open-questions.md)
lists known discrepancies without inventing new release blockers.

Before proposing a release, follow the [Release Process](release.md).

The finite installed-interface and fictional transformation/session acceptance
for stable 1.6.0 completed with [recorded limits](release-evidence-1.6.0.md).
Use the [acceptance matrix](acceptance-matrix.md) to plan new changes; prior
results do not approve later code or any dataset.

For versioned builds and offline exports, see
[Publishing Documentation](development/documentation.md).
