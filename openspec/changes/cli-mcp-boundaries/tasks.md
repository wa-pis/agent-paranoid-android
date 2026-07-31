# Tasks: cli-mcp-boundaries

- [x] Add contract coverage for parser defaults, aliases, help, and registered
  MCP tool schemas where current golden fixtures are incomplete.
- [x] Extract review-gated agent command registration behind the existing
  entry point.
- [x] Extract remaining dataset and utility command registration.
- [x] Extract CLI human and JSON presentation from application dispatch.
  - [x] Move shared CLI error and validation-result rendering behind a
    presentation module.
  - [x] Move remaining agent human and JSON rendering behind the same boundary.
  - [x] Move examples, audit verification, and doctor rendering behind the
    presentation boundary.
- [x] Separate generator MCP registration from application services.
- [x] Separate Trino MCP registration from allowlisted application services.
- [ ] Keep safety checks in core/application layers and test direct services.
- [ ] Update the implementation map, changelog, and relevant contributor docs.
- [ ] Run `scripts/check_release.sh`.
- [ ] Run `mkdocs build --strict`.
