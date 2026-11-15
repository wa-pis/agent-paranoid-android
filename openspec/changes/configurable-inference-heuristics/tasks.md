# Tasks: configurable-inference-heuristics

- [x] Record future scope and proposed capability requirements.
- [x] Inventory current inference entry points and supported metadata by source.
- [x] Implement version 1 for explicit profile-to-spec inference via Python,
      CLI and MCP: scoped literal suffix rules for synthetic string identifiers,
      and a confidence floor for inferred relationships. The initial suffix rules are additive. Bound rule count, selector length
      and field/rule evaluations; preserve reviewed inputs and protected fields.
- [x] Add explicit field actions, priorities, conflict rejection and a confidence
      floor for inferred constraints.
- [x] Record the options digest, winning rules and threshold effects in the
      DatasetSpec; its existing fingerprint binds the evidence to exact review.
      Inference runs after profile caching and does not cache configured results.
- [x] Test default compatibility, custom overrides, conflicts, invalid settings,
      bounded execution and privacy/approval rejection using fictional fixtures.
- [x] Verify equivalent metadata across sources, output formats and Python/CLI/MCP;
      report unavailable metadata explicitly and preserve business-rule enforcement.
- [x] Document runnable examples and run focused tests, strict OpenSpec validation
      and documentation checks before releasing the capability.

The initial implementation shipped in v1.7.0 via PR #704. To reproduce the
follow-up matrix, install the project with the development and all optional
extras in separate environments with MCP SDK 1 and 2, then run:

```sh
python -m pytest -o pythonpath= -q tests/test_inference_matrix.py tests/test_inference_options.py tests/test_source_output_matrix.py
```

Configured inference covers 288 generation routes per MCP SDK: eight safe
profile sources (CSV file/folder, Parquet, saved JSON, PostgreSQL/Trino
table/query), three spec encodings (JSON/YAML/YML), four exports
(CSV/JSON/Parquet/SQL), and Python/CLI/MCP. The matrix compares outputs with
equivalent metadata, checks provenance, protection of sensitive fields,
retention of declared relationships and confirmed constraints, and continued
business-rule validation. Absent null statistics and unsupported or unknown
SQL expression dependencies reject inference without writing a spec. The
database acquisition paths use fictional stand-ins. Existing reviewed JSON/YAML
specs bypass profile inference and remain covered by the separate generation
matrix. CLI and MCP option syntax is documented in the CLI workflows guide.
