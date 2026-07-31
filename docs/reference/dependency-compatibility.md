# Dependency Compatibility

Dependency versions can change parsing, generated values, serialization, SQL
policy, or validation without changing this package. The release evidence
therefore distinguishes a **minimum candidate** profile from the **latest
tested** lock. A profile is supported only after its CI job passes; declaring a
range in package metadata alone is not compatibility evidence.

## Semantic Dependency Inventory

| Dependency | Surface affected | Base or extra |
| --- | --- | --- |
| Faker | Seeded semantic values and locale behavior | Base |
| Pydantic | `DatasetSpec`, profile, manifest, and report parsing/validation | Base |
| PyYAML | YAML spec and business-rule parsing | Base |
| PyArrow | Parquet reading, writing, and schema conversion | `parquet` |
| MCP | Generator and Trino transport schemas | `mcp` |
| sqlglot | Read-only SQL parsing and policy enforcement | `trino` |
| Trino client | Connection construction and bounded query execution | `trino` |
| OpenAI | Optional advisor-provider request/response transport | `openai` |

Transitive packages are recorded by the lock and supply-chain evidence, but do
not receive an independent support promise unless they affect one of these
contract surfaces directly.

## Profiles

Minimum candidates match the lower bounds in `pyproject.toml`. Latest versions
are the versions in the reviewed `uv.lock` used by the release gate on
2026-08-01.

| Profile | Python | Direct dependency set |
| --- | --- | --- |
| `base-minimum` | 3.11 | Faker 25.0.0; Pydantic 2.7.0; PyYAML 6.0.0 |
| `parquet-minimum` | 3.11 | Base minimum; PyArrow 15.0.0 |
| `mcp-minimum` | 3.11 | Faker 25.0.0; Pydantic 2.8.0; PyYAML 6.0.0; MCP 1.0.0 |
| `trino-minimum` | 3.11 | Base minimum; sqlglot 30.0.0; Trino 0.330.0 |
| `openai-minimum` | 3.11 | Base minimum; OpenAI 2.46.0 |
| `latest-all` | 3.11–3.14 | Faker 40.35.0; Pydantic 2.13.4; PyYAML 6.0.3; PyArrow 25.0.0; MCP 1.28.1; sqlglot 30.13.0; Trino 0.338.0; OpenAI 2.50.0 |

MCP 1.0.0 requires Pydantic 2.8.0, so its minimum profile cannot reuse the
base Pydantic 2.7.0 candidate. The minimum profiles otherwise isolate one
optional extra at a time. `latest-all` tests the locked dependency set across
every supported Python version. The CI matrix installs these profiles without
silently upgrading minimum candidates and runs the contract tests relevant to
each surface.

## Contract Coverage

The minimum profiles run focused contracts instead of the full locked suite:

| Profile | Required behavior | CI contract |
| --- | --- | --- |
| `base-minimum` | Deterministic generation and validation; Pydantic JSON and PyYAML parsing | `tests/test_io_workflows.py`, `tests/test_business_rules.py` |
| `parquet-minimum` | Parquet serialization and loading | `tests/test_io_commands.py` |
| `mcp-minimum` | Generator and Trino MCP transport schemas | `tests/test_mcp_generator_transport.py`, `tests/test_mcp_trino_transport.py` |
| `trino-minimum` | SQL policy and Trino client construction | `tests/test_mcp_trino_server.py` |
| `openai-minimum` | Provider request, response, and error contracts | `tests/test_openai_provider.py` |

The `latest-all` quality matrix runs the complete test suite on every
supported Python version. A minimum profile must not be replaced by a resolver
check alone: its behavior contract must also pass in the isolated environment.

## Support Rules

- Same package, Python, dependency, locale, serializer, spec, rules, and seed
  provide the logical reproducibility baseline recorded in the manifest.
- Byte identity is checked only where an artifact digest is recorded; it is not
  promised across Python, package, dependency, locale, or serializer changes.
- A dependency update that changes parsing, generation, SQL policy, or
  validation semantics requires review, compatibility evidence, and a package
  release.
- Existing `<2` MCP and `<3` OpenAI bounds remain because those major versions
  are untested. No new upper major bound is implied for Faker, Pydantic, PyYAML,
  PyArrow, sqlglot, or Trino until minimum/latest matrix evidence justifies it.
- A failing profile is unsupported until fixed or explicitly removed from the
  documented range with release notes.

The lockfile is evidence for the latest profile, not a promise that unrelated
future dependency versions are compatible.
