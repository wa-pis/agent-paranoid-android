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

For the current source/output, business-rule and MCP work, complete the planned
[Final Acceptance Matrix](acceptance-matrix.md) after implementation stabilizes.
It separates existing unit coverage from installed CLI/Python/MCP, option,
permission, container and disposable-database acceptance. OpenSpec change
`cross-interface-acceptance` tracks the outstanding campaign; it is not yet run.
