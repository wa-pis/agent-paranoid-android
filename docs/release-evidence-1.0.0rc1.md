# 1.0.0rc1 Internal Release Evidence

This document preserves implementation, OpenSpec, audit, and release-engineering
facts removed from the user-facing `Unreleased` changelog during RC hygiene.
The source classification is recorded in the [inventory](unreleased-inventory-1.0.0rc1.md).
These facts are evidence for maintainers, not additional product guarantees.

## RC Gate Snapshot

The full local release gate passed on `main` commit
`c9a26b75b22296eea5448d62b6952cc773f88b94` on 2026-08-01. It covered Ruff,
strict mypy across 78 source files, compilation, 97 approved dependency
licenses, dependency compatibility, direct privacy and SQL boundaries,
operational budgets, schema freshness, and the synthetic quickstart. The test
run reported 537 passed, 3 skipped, and 88.01% coverage.

The equivalent reviewed tree passed 29 CI checks with four intentional skips
before merge. Evidence is retained in the [CI and wheel run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30678989489),
[container run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30678989496),
[documentation run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30678989523),
and [security run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30678989499).
This snapshot does not replace the final rerun against the exact release commit.

## Added-Scope Evidence

- Explicit direct-API privacy and SQL-boundary checks in the release gate.
- Staged timeout cleanup coverage for folder, review, and single-entity
  generation outputs.
- A real Parquet `doctor` capability smoke that generates and reads a temporary
  bundle with secret-free reinstall guidance on failure.
- A local MCP `doctor` capability smoke that constructs the generator
  transport and verifies audited tool registration without starting a server.
- A local Trino `doctor` capability smoke that validates allowlisted SQL and
  constructs a client without executing a query or contacting a coordinator.
- A local OpenAI `doctor` capability smoke that verifies the structured SDK
  surface and advisor construction without credentials or provider requests.
- Isolated base-wheel build, installation, metadata, size, and `doctor` smoke
  coverage on every supported Python version from 3.11 through 3.14.
- ARM64 pull-request build and hardened runtime health checks for every CLI,
  generator MCP, and Trino MCP container target.
- Blocking container scans for fixable High and Critical vulnerabilities in
  every native CLI and MCP target before publication.
- A fail-closed dependency-license gate for application, optional, development,
  and documentation environments without adding a scanner dependency.
- A dated security review with scanner evidence and explicit dispositions for
  all remaining OpenSSF Scorecard governance and maturity findings.
- Canonical OpenSpec requirements for behavior-preserving CLI boundaries and
  safety-equivalent direct/MCP application services, with the completed change
  archived for the 1.0 contract freeze.
- A canonical public-contracts OpenSpec capability covering retained aliases,
  wrappers, migration targets, and minimum deprecation windows.
- The completed public stability map merged into the canonical public-contracts
  OpenSpec capability and archived with its implementation evidence.
- The completed versioned golden-contract catalog merged into canonical
  OpenSpec and archived with its compatibility evidence.
- Previous feature-release fixture compatibility merged into canonical
  OpenSpec and archived with its immutable provenance evidence.
- Runtime, optional-extra, and provider-adapter support policy merged into
  canonical OpenSpec and archived with its release-gate evidence.
- A canonical public Python API capability covering reviewed top-level exports,
  with the completed golden-contract change archived.
- A canonical artifact-contract capability covering stable generation bundle
  filenames and metadata-only validation report fixtures.
- A canonical MCP interface capability covering stable discovery schemas and
  the default exclusion of unrestricted raw SQL.
- Cross-table average reconciliation merged into canonical synthetic-generation
  OpenSpec and archived with its deterministic and aggregate-only evidence.
- Controlled negative field and row-rule coverage merged into canonical
  synthetic-generation OpenSpec and archived with deterministic evidence.
- Controlled foreign-key and aggregate-formula negative cases merged into
  canonical synthetic-generation OpenSpec and archived with isolation evidence.
- Bounded expected-versus-observed negative validation artifacts merged into
  canonical synthetic-generation OpenSpec and archived with privacy evidence.
- CLI and generator MCP negative-case reproducibility merged into canonical
  synthetic-generation OpenSpec and archived with executable example evidence.
- A canonical operational-readiness capability covering bounded synthetic
  profiling, generation, and validation resource regression gates.
- Fail-closed path-aware CI classification that keeps strict documentation
  checks while skipping heavy Python, container, and security jobs for docs-only
  pull requests and main pushes.

## Fixed-Scope Evidence

- An end-to-end workspace flow uses a local fake advisor provider, stops for
  explicit approval, and verifies raw emails, rare text, and source identifiers
  never enter the provider exchange.
- Agent input detection requirements are merged into canonical orchestration
  OpenSpec and the completed change is archived with its implementation evidence.
- The completed provider-neutral advisor client adapter change is archived
  after confirming its trust-boundary contract is canonical.
- The completed review-gated reference agent flow is archived after confirming
  its runnable workflow requirement is canonical.
- The completed metadata-only agent review report is archived after confirming
  its detailed review contract is canonical.
- The completed container vulnerability gate is merged into canonical
  operational readiness OpenSpec and archived with its implementation evidence.
- The supported Python 3.11-3.14 wheel matrix is merged into canonical
  operational readiness OpenSpec and archived with its implementation evidence.
- The completed metadata-only agent review summary is archived after confirming
  its bounded review contract is canonical.
- All remaining completed pre-RC OpenSpec changes are consolidated into their
  canonical capabilities and archived as one reviewed documentation baseline.
- Lightweight no-op Python matrix checks for docs-only changes so existing
  branch-protection requirements are reported instead of remaining pending.
- The CSV profiler now runs under the project's strict type-checking gate.
- Strict type checking now covers the I/O package and Parquet adapter, with an
  explicit boundary for the optional untyped `pyarrow` dependency.
- Strict mypy now covers the complete production package and both contract
  fixture scripts.
- Pre-RC release documentation records the passing 87.94% unit, property, and
  contract coverage gate against an exact `main` commit.
- The RC roadmap now requires runnable, CI-verified examples for CSV,
  relational rules, local Trino, MCP, Python API, and supported exports.
- A versioned delivery plan from `0.13.0` through `1.0.0`, with explicit scope,
  exit criteria, release gates, and deferred work.
- An ordered remaining-work checklist from completed feature scopes through
  OpenSpec closure, RC security review, public artifact verification, and 1.0.
