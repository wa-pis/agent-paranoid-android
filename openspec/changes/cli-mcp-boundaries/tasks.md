# Tasks: cli-mcp-boundaries

- [ ] Add contract coverage for parser defaults, aliases, help, and registered
  MCP tool schemas where current golden fixtures are incomplete.
- [ ] Extract CLI parser construction behind the existing entry point.
- [ ] Extract CLI human and JSON presentation from application dispatch.
- [ ] Separate generator MCP registration from application services.
- [ ] Separate Trino MCP registration from allowlisted application services.
- [ ] Keep safety checks in core/application layers and test direct services.
- [ ] Update the implementation map, changelog, and relevant contributor docs.
- [ ] Run `scripts/check_release.sh`.
- [ ] Run `mkdocs build --strict`.
