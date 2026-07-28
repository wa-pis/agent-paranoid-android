# Roadmap

The roadmap is ordered by safety and integration value, not by a fixed delivery
date.

## Implemented For 0.8.1

- AI prompts and integration documentation aligned with the implemented
  `DatasetSpec`, output-format, approval, and artifact-only MCP contracts.
- Independent installation smoke tests for the base package and the `parquet`,
  `mcp`, and `trino` extras.
- Dependency-count and wheel-size budgets that keep optional integrations out
  of the base installation.
- `all` documented as a development, demo, and container convenience.
- Strict type checking for the CLI and agent-facing interfaces, with typed
  plan and generation summaries.

## Implemented Toward 0.9.0

- Read-only workspace status for the review-first agent flow, including
  versioned JSON output for automation and AI clients.
- Narrow validated `agent-plan` input detection for CSV files, CSV folders,
  and safe profiles, with DatasetSpec inputs routed to `generate`.

## Implemented For 0.8.0

- Separate minimal CLI, generator MCP, and Trino MCP OCI images.
- A least-privilege Compose deployment with non-root workers, read-only root
  filesystems, bounded resources, mounted audit secrets, and isolated
  generator networking.
- Multi-platform GHCR publication with BuildKit SBOM and provenance,
  GitHub attestations, and keyless Cosign signatures.

## Implemented For 0.7.0

- Lightweight base installation with explicit `parquet`, `mcp`, `trino`, and
  `all` extras.
- Review-first allowlisted Trino planning through MCP without raw-SQL access
  on the default tool surface.
- HMAC-authenticated, metadata-only MCP audit records with integrity
  verification and bounded fail-closed storage.
- An explicit compatibility and deprecation policy for future DatasetSpec
  `schema_version` revisions.

## Implemented For 0.6.0

- One reviewed `DatasetSpec` contract across CLI and Python generation and
  validation workflows.
- Removal of the deprecated parallel specification API and conversion layer.
- Consistent `dataset_spec.json` and `dataset_spec.yaml` artifact names.
- A smaller project README backed by the published task-oriented documentation
  site.

## Implemented For 0.5.1

- Tokenless PyPI publication with post-publish digest comparison and a clean
  public-index installation smoke test.
- OpenSSF Scorecard reporting and expanded standard project links on PyPI.

## Implemented For 0.5.0

- Structured generator MCP business-rule inputs with strict contract checks,
  sensitive-literal rejection, bounded formulas, manifest fingerprints, and
  compact validation summaries.
- Typed package metadata, strict core/rules/MCP type checks, installed-wheel
  smoke coverage, and pull-request dependency review.

## Completed In 0.4.0

- Content-aware PII and secret detection across CSV, Trino, and imported
  profile trust boundaries.
- Configurable input, output-size, disk-reserve, execution-time, and Trino
  server-side query budgets.
- Locked dependencies, vulnerability auditing, CodeQL, full-history secret
  scanning, and live Trino integration coverage.
- Reproducible release artifacts with CycloneDX SBOMs, checksums, provenance,
  and SBOM attestations.

## Completed In 0.3.0

- Full MCP workflow for safe CSV profiling, spec inference, deterministic
  generation, validation, and export.
- Direct safe-profile handoff between Trino and generator MCP tools.
- Versioned DatasetSpec contract and auditable generation manifests.
- Runtime raw-profile and source-row reuse protections.
- End-to-end AI integration demo.
- Review-first agent orchestration with `agent-plan` and `agent-approve`.

## MVP Freeze

Keep the current MVP focused on the reliable golden path:

- CSV file or CSV folder input.
- Safe profile metadata, not source rows.
- Reviewable `DatasetSpec`.
- Deterministic generation by explicit seed.
- CSV, JSON, and Parquet export.
- Validation report and generation manifest.
- MCP responses that return summaries and artifact paths, not dataset rows.

Treat these as non-negotiable release gates rather than new feature work:

- `ruff`, `compileall`, and the full pytest suite pass.
- Quickstart commands in README run against checked-in fixtures.
- Generated manifests report `synthetic: true` and
  `source_rows_copied: false`.
- OpenSpec baseline stays aligned with implemented behavior.

## Planned For 0.9.0

Make the review-first agent workflow the clearest product entry point:

- Provide a small guided command set for planning, reviewing, approving, and
  checking the status of a generation run. Initial workspace status inspection
  is implemented; guided planning and review remain.
- Detect CSV files, CSV folders, safe profiles, and `DatasetSpec` inputs when
  this can be done unambiguously, while retaining explicit overrides. CSV and
  profile detection is implemented; DatasetSpec inputs are recognized and
  routed to the existing reviewed-spec workflow.
- Present concise human-readable summaries of inferred fields, sensitive
  fields, relationships, confidence, assumptions, and safety warnings.
- Add stable JSON output for automation and AI clients, with documented exit
  codes and structured errors.
- Introduce typed plan, run, approval, and error models with a plan identifier,
  profile/spec fingerprints, and an approval receipt tied to the reviewed
  `DatasetSpec`.
- Make interrupted or repeated operations observable and safely recoverable
  through explicit status and idempotent state transitions.
- Add high-level MCP workflow tools so an AI client does not need to choose
  manually among every low-level profiling operation for the common path.
  Keep advanced profiling tools available without weakening the current Trino
  and generator-server trust boundary.

## Reference AI Agent

Provide a practical AI-agent integration without coupling the deterministic
core to one model vendor:

- Define a provider-neutral advisor interface that accepts safe profile
  metadata and proposes structured `DatasetSpec` changes.
- Validate every model-produced proposal with Pydantic and the existing
  deterministic safety, generation, and validation layers.
- Keep model SDKs out of the base package; ship provider integrations as
  optional examples or separate extras only when they are useful.
- Ensure the model never needs raw production rows, raw PII, database
  credentials, unrestricted SQL, or generated dataset contents in chat.
- Treat table names, column names, descriptions, and safe distribution values
  as untrusted data and defend the agent flow against prompt injection.
- Include a complete reference flow that profiles, proposes a spec, requests
  human approval, generates, validates, and reports artifact paths and
  manifest facts.

## Dependency Policy

- Keep the base runtime limited to dependencies required for deterministic
  generation and strict contracts. `Faker`, `Pydantic`, and `PyYAML` are the
  current direct baseline.
- Keep Parquet, MCP, and Trino support in separate extras. Do not require
  `PyArrow`, the MCP SDK, the Trino client, or SQL parsing for basic CSV/JSON
  generation.
- Do not replace maintained protocol or database libraries with custom
  implementations solely to reduce package count.
- Measure the base environment separately from development and `all` installs
  in CI, and document the installation cost of each optional capability.

## Toward 1.0

- Stabilize the public Python, CLI, MCP, `DatasetSpec`, and artifact contracts.
- Split the CLI and MCP server modules into parsing, application, and
  presentation boundaries without changing their safety behavior.
- Remove legacy compatibility wrappers and command aliases only after a
  documented deprecation period.
- Add a pluggable semantic-provider interface for organization-specific
  synthetic values without allowing providers to bypass privacy validation.
- Expand cross-table aggregate constraints and controlled negative scenarios.

## Later

- Deployment templates for orchestrators beyond Docker Compose.
