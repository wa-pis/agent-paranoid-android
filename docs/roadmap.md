# Roadmap

The roadmap is ordered by safety and integration value, not by a fixed delivery
date.

## Completed In 0.3.0

- Full MCP workflow for safe CSV profiling, spec inference, deterministic
  generation, validation, and export.
- Direct safe-profile handoff between Trino and generator MCP tools.
- Versioned DatasetSpec contract and auditable generation manifests.
- Runtime raw-profile and source-row reuse protections.
- End-to-end AI integration demo.

## Next

- Expose structured business-rule configuration through the generator MCP
  server and include business validation in the generation manifest.
- Add an optional orchestration tool that profiles an allowlisted Trino table,
  builds a reviewable DatasetSpec, and stops before generation for approval.
- Add configurable output quotas for row counts, total artifact size, and
  execution time.
- Add signed or externally persisted audit records for teams running the MCP
  servers in shared environments.
- Publish a formal DatasetSpec JSON Schema and compatibility policy for future
  `schema_version` revisions.

## Later

- Pluggable synthetic providers for organization-specific semantic types.
- More cross-table aggregate constraints and controlled negative scenarios.
- Packaging and deployment examples for isolated MCP workers.
