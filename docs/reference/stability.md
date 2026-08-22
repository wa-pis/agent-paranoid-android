# Public Stability

This page defines the supported integration surfaces at and after the `1.0`
compatibility baseline. "Supported" means changes are reviewed against the
listed contract gate and announced when migration is required. It does not
mean that every internal module is public. Provider adapters remain
experimental unless a later feature release promotes one explicitly.

## Stability Table

| Surface | Status | Owner | Compatibility rule | Contract gate |
| --- | --- | --- | --- | --- |
| Top-level Python imports in `test_data_agent.__all__` | Supported | `src/test_data_agent/__init__.py` | Additive exports are allowed; removal, rename, or incompatible signature changes are breaking | `public-python-api.json`, `test_contract_fixtures.py` |
| `test-data-agent` commands, options, aliases, JSON success/errors, doctor states, completion inventory, and exit codes | Supported | `cli.py`, `cli_parser.py`, `cli_presenter.py` | New optional commands/options are additive; rename, removal, changed default, output shape, or exit-code meaning is breaking | `cli-parser-surface.json`, CLI parser and presenter tests |
| Generator MCP tools and schemas | Supported | `mcp_generator_server.py`, `mcp_generator_transport.py` | New optional fields or tools are additive; removed tools, required fields, schema narrowing, or changed safety semantics are breaking | `mcp-generator-tools.json`, generator MCP tests |
| Trino MCP tools and schemas | Supported | `mcp_trino_server.py`, `mcp_trino_transport.py` | New bounded metadata fields or allowlisted tools are additive; removed tools, required fields, schema narrowing, or weaker safety defaults are breaking | `mcp-trino-tools.json`, Trino MCP tests |
| `DatasetSpec` YAML/JSON | Versioned | `core/dataset.py` | Optional fields with safe defaults require a schema minor version; removed, required, narrowed, or reinterpreted fields require a schema major version | JSON Schema, `dataset-spec.json`, DatasetSpec contract tests |
| Advisor request, exchange, and proposal JSON | Versioned | `advisor.py` | Optional metadata is additive; trust-channel, fingerprint, required-field, or proposal-validation changes are breaking | `advisor-exchange.json`, advisor contract tests |
| Generated bundle filenames and manifest/report JSON | Supported | `io/artifacts.py`, `io/workflows.py` | New optional files or fields are additive; renamed/removed files, required fields, or changed field meaning are breaking | `artifact-layout.json`, `generation-manifest.json`, `validation-report.json` |
| Provider adapters and runnable examples | Experimental | `providers/`, `examples/` | May evolve between feature releases; deterministic core contracts and safety rules still apply | Provider tests, documentation smoke tests |

The module paths in the owner column identify maintenance ownership, not
additional public imports. Import internal modules only when the relevant API
reference explicitly documents them.

## 1.3.0 Database Source Additions

Credential-free JDBC-style endpoint input, qualified column wildcards,
`profile-query`, and the top-level `SqlQueryProfileRequest` query-profiling
exports are supported in stable `1.3.1`. Existing component configuration,
exact allowlists, PostgreSQL profiling, and Trino safety behavior remain
unchanged.

## Artifact Persistence Boundary

The supported artifact contract distinguishes three properties:

| Property | Supported behavior |
| --- | --- |
| Atomic visibility | Completion-state and advisor-handoff files that use atomic writers are written beside the destination and replaced atomically. New folder, review, and agent-plan bundles are staged as siblings and published with one directory rename. Standalone artifact commands and multi-file updates are not covered by one global atomic transaction. |
| Process-interruption recovery | Catchable failures and interactive cancellation remove staging data or roll back moved files. Single-entity generation publishes its manifest last, validates format/suffix agreement, and permits replacement only of the same complete manifest-owned bundle. Agent completion can stop between its separately atomic receipt and result markers; `agent-status` and `agent-recover` revalidate the unchanged generated bundle before completing metadata publication. |
| Crash or power-loss durability | Not guaranteed. Artifact writers do not flush file contents and parent-directory metadata with `fsync`, so a hard process stop, kernel or host failure, storage failure, or power loss may leave staging data or lose a recently renamed artifact. |

A single-entity update inside an existing directory moves several files and is
not one filesystem transaction; its rollback applies only while the process
can handle the failure. The artifact `fsync` work is deferred until after 1.0
and is not an RC4 or stable-1.0 release blocker because crash/power-loss
durability is not part of the supported contract. See
[Operational Resource Budgets](../operations/resource-budgets.md#artifact-persistence-contract)
for the disposition and operator guidance.

## Change Classification

An additive change:

- preserves every existing valid input and documented output meaning;
- adds only optional fields with safe defaults;
- does not change command defaults, exit-code meaning, file names, or tool
  safety boundaries;
- keeps older clients able to ignore the addition.

A breaking change includes:

- removing, renaming, or narrowing an import, command, option, tool, field, or
  artifact;
- changing a default, exit code, field meaning, trust boundary, or validation
  behavior relied on by supported clients;
- making an optional field required;
- accepting data that a safety boundary previously rejected.

Bug and security fixes may intentionally reject previously accepted unsafe or
invalid input. Release notes must identify the affected surface and migration
path.

## Review Gate

Every public contract change must:

1. identify the affected row in the table;
2. classify the change as additive or breaking;
3. update OpenSpec, documentation, changelog, and the owning tests;
4. regenerate golden fixtures only after reviewing the semantic diff;
5. use a release that matches the compatibility impact.

Run `python3 scripts/update_contract_fixtures.py` only for an intentional,
reviewed contract change. A fixture update is evidence of a changed contract,
not approval to change it.

`tests/fixtures/contracts/contract-catalog.json` versions every golden JSON and
MCP fixture. `additive_only` entries cannot remove, rename, narrow, or require
existing fields without a breaking release. `schema_versioned` entries must
advance their serialized schema version and provide migration guidance for a
breaking change. Contract tests reject fixtures missing from this catalog.

Immutable baselines under `tests/fixtures/compatibility/vX.Y.Z/` come from an
annotated previous feature-release tag. Current readers and generators must
accept those reviewed specs and metadata. These baselines are copied with
provenance and are never regenerated by current models.

See [DatasetSpec Compatibility](../concepts/dataset-spec-compatibility.md) for
schema-version and deprecation rules. See
[Runtime And Integration Support](support-policy.md) for supported Python
versions, optional extras, and provider-adapter maturity.
