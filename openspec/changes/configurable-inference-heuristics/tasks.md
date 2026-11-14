# Tasks: configurable-inference-heuristics

- [x] Record future scope and proposed capability requirements.
- [x] Inventory current inference entry points and supported metadata by source.
- [x] Implement version 1 for explicit profile-to-spec inference via Python,
      CLI and MCP: scoped literal suffix rules for synthetic string identifiers,
      and a confidence floor for inferred relationships. Rules are additive and
      cannot conflict in this first version. Bound rule count, selector length
      and field/rule evaluations; preserve reviewed inputs and protected fields.
- [ ] Design broader rule actions and incompatible-proposal diagnostics.
- [ ] Add effective-config fingerprints.
- [ ] Integrate provenance, cache invalidation and existing review bindings.
- [ ] Test default compatibility, custom overrides, conflicts, invalid settings,
      bounded execution and privacy/approval rejection using fictional fixtures.
- [ ] Verify equivalent metadata across sources, output formats and Python/CLI/MCP;
      report unavailable metadata explicitly and preserve business-rule enforcement.
- [ ] Document runnable examples and run focused tests, strict OpenSpec validation
      and documentation checks before releasing the capability.
