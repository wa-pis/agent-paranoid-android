# Runtime And Integration Support

This policy defines which Python runtimes, optional capabilities, and model
provider adapters the project supports. It complements the
[Public Stability](stability.md) contract map; it does not make internal
modules public.

## Python Versions

The package supports CPython 3.11, 3.12, 3.13, and 3.14. Each supported
version runs the test suite and builds, installs, and checks an isolated base
wheel before release. Alternative Python implementations may work, but are not
release-gated.

- Python 3.11 is the current minimum and remains supported through the 1.x
  series unless a security or dependency constraint makes that impossible.
- A newly released CPython version becomes supported only after it is added to
  the CI matrix and the wheel smoke test passes.
- Dropping a Python version is a breaking packaging change. It requires release
  notes, migration guidance, and at least one feature-release notice before the
  new `requires-python` constraint takes effect.
- Security fixes may shorten that notice when the older runtime cannot be
  supported safely; the release notes must explain the exception.

## Optional Extras

The base installation is the supported deterministic CSV and JSON core.
Optional extras are supported capabilities, but users install and operate only
the capabilities they need.

| Extra | Supported capability | Release gate |
| --- | --- | --- |
| `parquet` | Parquet import and export | isolated wheel install, `doctor --require-extra parquet`, Parquet tests |
| `mcp` | Generator MCP transport | isolated wheel install, `doctor --require-extra mcp`, MCP contract tests |
| `trino` | Read-only Trino client and safe SQL parsing | isolated wheel install, `doctor --require-extra trino`, mocked and live opt-in Trino tests |
| `postgres` | Read-only allowlisted PostgreSQL profiling driver; deterministic PostgreSQL SQL export remains in base | isolated wheel install, `doctor --require-extra postgres`, fake-driver tests, and opt-in disposable execution example |
| `openai` | Reference OpenAI advisor adapter | isolated wheel install, `doctor --require-extra openai`, fake-transport provider tests |
| `gigachat` | Experimental GigaChat advisor through the official SDK | isolated wheel install, `doctor --require-extra gigachat`, fake-SDK provider tests |
| `all` | Development, demos, and container builds | full install and container smoke tests; not recommended for normal users |

Removing an extra, moving a base capability behind an extra, or making one
extra unexpectedly require another is a breaking packaging change. Adding an
extra or adding an optional dependency inside an existing extra is additive
when its documented behavior and security boundary remain unchanged.

The database-source additions on unreleased `main` use the existing
`postgres` and `trino` extras. They add no JVM or JDBC driver. JDBC-style URL
support is endpoint syntax only, qualified wildcards expand into explicit
columns, and `profile-query` requires the safe SQL parser bundled with the
selected database extra. These additions are not part of the published stable
`1.2.0` support contract until the next feature release candidate is accepted.

Dependencies within an extra may receive compatible updates between feature
releases. The lock file, dependency review, vulnerability audit, and isolated
installation checks are the release evidence; arbitrary combinations outside
the declared dependency ranges are not supported.

## Provider Adapters

The provider-neutral `DatasetAdvisor`, `AdvisorExchange`, and
`AdvisorProposal` contracts are versioned public surfaces. They remain
separate from model SDKs and never grant approval, generation, filesystem, or
database access.

Provider-specific adapters, including the bundled OpenAI reference adapter
and experimental GigaChat adapter, remain experimental unless the stability
table explicitly promotes them. They may change between feature releases as
provider APIs evolve, while these requirements remain mandatory:

- requests contain safe metadata only, never source rows, raw PII, secrets,
  credentials, or generated dataset contents;
- provider output is bounded and validated against the original fingerprint;
- provider SDKs stay in provider-specific extras, outside the base package;
- tests use local fakes and do not contact real provider services;
- errors exposed to users and logs are secret-free.

An adapter becomes supported only when the stability table marks it supported,
its optional extra has an isolated installation gate, and its contract tests
cover request mapping, output validation, error redaction, and dependency
absence from the base package. Deprecating a supported adapter requires the
same notice and migration rules as other supported public surfaces.

Custom adapters are application-owned. The project supports their use of the
documented provider-neutral contract, but cannot guarantee a third party's
transport, SDK, availability, pricing, or data-retention behavior.

## Reporting Problems

Include the package version, Python version, installed extras, platform, and a
minimal synthetic reproduction. Never attach production rows, raw PII,
credentials, provider responses containing sensitive data, or audit keys.
