# Pre-1.0 Release Candidate History

This archive preserves the detailed `1.0.0` release-candidate notes moved from
the main changelog. Stable release notes remain in
[CHANGELOG.md](https://github.com/wa-pis/agent-paranoid-android/blob/main/CHANGELOG.md).

## [1.0.0rc6] - 2026-08-11

### Added

- Add an allowlist-only `profile-postgres` CLI workflow that writes safe
  metadata and bounded aggregate profiles through the optional PostgreSQL driver.
- Add a typed field-scoped local category allowlist across CSV, folder, agent,
  CLI, profile, and generation-spec boundaries without weakening default
  category replacement.
- Add `export-postgres-sql` for one deterministic, atomically published
  PostgreSQL transaction containing quoted DDL, foreign keys, and INSERT
  statements generated from validated synthetic records.
- Add complete PostgreSQL and Trino guides plus runnable synthetic local
  examples for disposable profiling, generation, validation, and SQL execution.
- Add field-scoped, collision-safe placeholders for rare categorical values.
- Add typed per-call OpenAI structured completion results and failure metadata;
  retain `last_run_metadata` only as a legacy compatibility view.
- Add `trusted-local` and `shared-hardened` Trino deployment profiles, with a
  required finite cumulative scan ceiling for shared environments.
- Add bounded Trino deployment profile and effective scan-limit status to
  `doctor`.

### Changed

- Restore field-and-destination privacy policy: preserve explicitly allowlisted
  safe business enums locally, keep sensitive and unknown fields transformed,
  and keep every external-provider category source-literal free.
- Bind review-first CSV agent plans and final no-copy validation to the exact
  source version captured before profiling, rejecting changed or legacy
  unbound plans before publication.

### Fixed

- Validate JSON dataset fields by membership rather than object-key order, so
  deterministic sorted-key artifacts pass the documented standalone
  validation command.

### Security

- Document four accepted Low security findings with exact identities, risk
  ownership, revisit triggers, and a first post-1.0 hardening target.
- Pin the Dockerfile frontend to the immutable multi-platform digest behind
  `docker/dockerfile:1.7`.
- Bind single-CSV no-copy validation to SHA-256 row digests collected during
  the same read that produced the profile, so path replacement cannot switch
  the checked source before publication.
- Reject entity names reserved for generation control artifacts during spec
  validation and again before any dataset file is written.
- Reject duplicate entity stems across CSV, JSON, and Parquet dataset folders
  before any row artifact is read.
- Check local CSV profiling deadlines between individual field-processing and
  field-finalization operations.
- Reserve bounded terminal audit capacity before MCP tool execution so a full
  log rejects admission instead of losing the completion event.
- Replace source-derived CSV-folder text categories with collision-safe rank
  labels before caching, spec inference, or generation while preserving counts
  and conditional-rule semantics.
- Replace source-derived advisor constraint literals with the same field-scoped
  category labels, reject unrepresented strings, and preserve executable
  conditions across persisted-review verification.
- Replace every provider-bound categorical JSON scalar with a deterministic
  field-scoped label while preserving numeric distribution bounds.
- Recursively mask strings in bounded composite `run_safe_select` values so
  nested Trino maps, arrays, and rows cannot bypass the opt-in row policy.
- Prevent equal rare values in different fields from sharing a synthetic
  placeholder and prevent placeholders from colliding with normal categories,
  including placeholder-shaped baseline literals, while preserving sanitizer
  provenance across reordered baseline categories.
- Keep provider metadata attached to the invocation that produced it, including
  preflight and provider-error paths, without retaining prompts or source data.
- Detach handled OpenAI provider and validation failures from their original
  cause/context chains, and replace incomplete-response status text with a
  fixed bounded local error.
- Reject advisor formulas with string constants, unknown or incompatible
  references, and protected targets; enforce fixed post-solve type and privacy
  checks before generated rows reach publication adapters.
- Run generator MCP over the bounded stdio transport with fresh shared request
  budgets, bounded final responses, and pre-materialization JSON structure
  limits.
- Restrict public artifact names to safe path components, neutralize
  spreadsheet formula markers in CSV cells, and replace formula diagnostics
  with fixed local reasons.
- Bound active MCP requests and shared Trino operations process-wide, return a
  fixed capacity error, and release admission state on every terminal path.
- Replace backend-controlled Trino failures with a fixed detached MCP error and
  expose catalog/schema discovery only through configured allowlists.
- Mask every string returned by the explicit opt-in `run_safe_select` surface,
  including names and addresses missed by heuristic classification.
- Isolate semantic-provider calls behind a fixed deadline, require matching
  same-seed replay, and restrict string output to the `synthetic_` namespace.
- Publish files, folders, caches, and agent workspaces through one no-follow,
  descriptor-relative path policy that revalidates inode identity before
  replacement and cleanup.
- Publish single-entity manifests last, verify recorded artifact hashes before
  reporting completion, and require explicit overwrite approval for every
  replaced sibling artifact.
- Escape and bound untrusted CLI diagnostics, paths, provider metadata, and
  row-count labels, while preserving structured JSON errors and bounded
  canonical audit records.
- RC6 acceptance additionally requires source-free external advisor payloads,
  suppression of exact sensitive numeric profile metrics, semantically
  validated provider constraints, bounded generator MCP framing and JSON
  materialization, bounded active requests, explicit opt-in row privacy,
  semantic-provider and filesystem boundaries, safe CSV/artifact boundaries,
  escaped diagnostics, trusted release identity, and external acceptance
  evidence.

## [1.0.0rc5] - 2026-08-08

### Added

- Add bounded typed OpenAI advisor settings for model, reasoning effort,
  input bytes, output tokens, timeout, retries, and optional service tier.
- Add bounded in-memory OpenAI advisor run metadata for settings, sizes,
  latency, status, provider-reported retries, and token usage.
- Add a separate OpenAI relationship-candidate ranking adapter that accepts
  only bounded deterministic candidates and returns review-required proposals.
- Add explicit bounded fast, normal, and quality OpenAI advisor candidate
  presets without changing constructor defaults before benchmark evidence.
- Add a synthetic-only OpenAI advisor preset benchmark runner with explicit
  pricing inputs and redacted aggregate quality, latency, usage, and cost data.
- Expand the advisor acceptance runner to five synthetic profile shapes and an
  explicit bounded run count with p50/p95, error, retry, token, and cost metrics.

### Changed

- Use GPT-5.6 reasoning effort `none` for the fast advisor candidate while
  retaining the legacy typed `minimal` value for compatibility.
- Select the benchmark-backed fast advisor settings as the constructor defaults:
  4,096 output tokens, a 15-second timeout, and no SDK retries.
- Complete the 60-call RC5 advisor acceptance benchmark across five synthetic
  profile shapes with 100% validity and safety preservation, no errors or
  timeouts, and aggregate latency, token, retry-reporting, and cost evidence.

### Fixed

- Send the advisor's public free-form-compatible JSON Schema in non-strict mode
  and fail closed through local typed validation of every provider response.

### Security

- Bound JSON-RPC request IDs by their serialized UTF-8 size before they can be
  reflected in Trino MCP success or error responses.
- Replace oversized Trino MCP responses with a fixed bounded JSON-RPC error and
  reject transport-response limits too small to reserve that error.
- Cover wide-row database overflow and final JSON-RPC growth from nested
  metadata and escaping with explicit response-budget regression tests.
- Add typed cumulative profiled-column, invocation-deadline, and optional
  estimated-scan limits to the shared Trino invocation budget.
- Set benchmark-backed Trino invocation defaults of 100 profiled columns, 150
  statements, and 120 seconds.
- Enforce profiled-column, statement, deadline, and conservative scan estimates
  through one monotonic budget across nested Trino table profiling.
- Clamp Trino HTTP, execution, and run timeouts to the remaining invocation
  deadline and close active query resources when it expires.
- Add fail-closed environment configuration and scope documentation for Trino
  invocation column, statement, deadline, and optional scan limits.
- Bound each fresh local CSV-folder profile with typed deadline, sample, input
  byte, and cell limits, leaving no partial metadata cache after exhaustion.
- Count trusted instructions, untrusted metadata, structured-output schema,
  settings, and serialization in the OpenAI advisor request budget.
- Reject non-protocol JSON-RPC request IDs before dispatch and isolate active
  request budgets by exact serialized ID type and value.

## [1.0.0rc4] - 2026-08-02

### Changed

- Remove the `sample_rows_masked` Trino MCP tool, masking-service method, and
  query builder from the RC4 compatibility surface.
- Pin RC4 installation guidance and optional extras to `1.0.0rc4`, with a
  tag-matched clean-environment README smoke gate for the public wheel.
- Verify installed-wheel CSV and JSON quickstarts without optional integration
  dependencies, and isolate Trino-extra failures in a separate CI check.
- Document the exact aggregate-only default Trino MCP surface and classify the
  separately enabled safe-select rows as potentially containing source values.
- Define atomic visibility and process-interruption recovery separately from
  crash durability, with artifact fsync explicitly deferred until after 1.0.
- Define stable 1.0 promotion as the accepted RC4 production tree plus only
  reviewed version, changelog, and release-metadata updates; any code or
  dependency change requires another release candidate.

### Security

- Remove the row-returning diagnostic path instead of relying on heuristic
  masking to prevent unknown source literals from reaching MCP clients.
- Create a concurrency-isolated work budget for every Trino MCP invocation and
  reject canonical application arguments over 256 KiB before tool execution.
- Reject raw Trino MCP stdio payloads over 1 MiB before JSON-RPC argument
  parsing, without retaining the complete oversized frame in memory.
- Bound cumulative SQL and formula character work before Python/sqlglot
  parsing and before opening a Trino connection.
- Bound cumulative Python and sqlglot AST nodes and maximum depth before
  formula rendering, policy traversal, or Trino query execution.
- Bound cumulative explicit SQL projections before opening a Trino connection
  and fail closed when a projection wildcard has unknown width.
- Bound cumulative parsed SQL statements before opening a Trino connection or
  cursor.
- Consume Trino response metadata and rows incrementally against the shared
  byte budget before retaining a complete oversized result.
- Share one monotonic budget across nested table/column profiling and opt-in
  safe SELECT execution, stopping before later Trino work after exhaustion.

### Migration

- MCP clients that called `sample_rows_masked` must use metadata and aggregate
  profiling tools such as `describe_table`, `profile_table_safe`, and
  `profile_column`. The separate `run_safe_select` tool remains explicit
  operator opt-in and is not a source-literal-free replacement.

## [1.0.0rc3] - 2026-08-02

### Added

- Add a manual post-publish gate that verifies immutable GitHub Release, PyPI,
  documentation, and signed multi-platform GHCR artifacts, then exercises
  agent approval and audit verification from the public wheel.

### Changed

- Preserve public Python, CLI, MCP, artifact, error, and safety contracts while
  moving workspace, agent lifecycle, CLI, and Trino ownership behind typed
  application boundaries. No user migration is required.

### Security

- Enforce spec safety inside the agent approval service before calling an
  injected generation port.
- Reject symlinked agent workspace targets at the persistence boundary before
  creating plan staging artifacts.

## [1.0.0rc2] - 2026-08-01

### Fixed

- Publish release-candidate container images with their PEP 440 package version
  while reserving floating major, minor, and `latest` tags for stable releases.

## [1.0.0rc1] - 2026-08-01

### Added

- Added a [disposable local Trino journey](https://github.com/wa-pis/agent-paranoid-android/tree/main/examples/local_trino) that
  profiles the built-in synthetic TPC-H catalog through bounded operations
  before generating fresh rows.
- Added a [runnable stdio MCP journey](https://github.com/wa-pis/agent-paranoid-android/tree/main/examples/mcp_stdio) using both
  installed servers, review-bound generation, and a disallowed Trino request
  rejected before network access.
- Added deterministic SQL `INSERT` export with quoted identifiers, escaped
  literals, manifest evidence, and a
  [runnable all-format example](https://github.com/wa-pis/agent-paranoid-android/tree/main/examples/output_formats).
- Added [canonical dependency identities](../reference/dependency-compatibility.md)
  and a stable dependency fingerprint to generation-manifest reproducibility
  evidence.
- Added an offline `test-data-agent demo --output PATH` workflow using a
  bundled fictional fixture, deterministic seed, and atomic artifact publish,
  plus product-fit guidance comparing alternative test-data approaches.
- Added metadata-only effective generation and business-rule evidence to
  generation manifests, bound to exact spec and rule fingerprints.
- Added bounded numeric distribution scaling with fail-closed non-identity
  scaling for sensitive synthetic totals.
- Added domain-agnostic business-invariant coverage for component formulas,
  partitions, temporal windows, paired values, grouped totals, relationship
  coverage, and cross-table reconciliation across multiple domains.
- Added metadata-only temporal relationship candidates with normalized range
  overlap evidence and no provider-visible source date bounds.
- Added relationship-discovery coverage for compatible key types, normalized
  cardinality/null/distinctness evidence, and ambiguous low-confidence cases.
- Added metadata-only relationship candidate mining, provider ranking validation,
  and explicit human review records that cannot authorize generation.
- A runnable single-table CSV example now exercises explicit profiling, spec
  inference, deterministic generation, and independent validation.
- A runnable relational CSV example now verifies generated foreign keys,
  deterministic business rules, and multi-table validation.
- A runnable public Python API example now demonstrates metadata-only spec
  inference, seeded bundle generation, and independent validation.
- Provider-neutral relationship discovery candidate and proposal contracts
  restricted to bounded safe metadata and mandatory human review.
- Public relational-synthesis contract defining preserved graph, distribution,
  temporal, and business-rule semantics and explicit non-guarantees.
- Public conduct, support, governance, and code-ownership policies for the
  current single-maintainer project model.
- Generation manifests now record bounded reproducibility inputs and output
  SHA-256 evidence while distinguishing logical from cross-version byte-level
  reproducibility.
- Cross-table average aggregate mappings across deterministic generation,
  validation, safe profile inference, and read-only Trino profiling.
- Deterministic controlled negative generation across required, allowed-value,
  numeric-bound, conditional, temporal, and formula business rules.
- Coordinated negative foreign-key and concrete-field aggregate-formula cases
  that preserve unrelated rows and parent tables.
- Bounded expected-versus-observed violation counts in business-validation
  reports and generation manifests for controlled invalid datasets.
- A checked-in controlled-invalid example with tested CLI/MCP reproducibility
  from one spec, rule file, seed, mode, and invalid ratio.
- A public stability table mapping Python, CLI, MCP, `DatasetSpec`, advisor,
  and artifact contracts to owners, compatibility rules, and test gates.
- A versioned catalog covering every golden JSON and MCP fixture with enforced
  additive-only or schema-versioned change rules.
- A compatibility inventory for retained CLI aliases, legacy Python wrappers,
  transitional model access, migration targets, and minimum support windows.
- Immutable `v0.11.0` spec and manifest fixtures proving current readers and
  deterministic generation remain compatible with the previous feature release.
- A public support policy for CPython versions, optional extras, provider
  adapter maturity, compatibility notices, and release gates.
- Bounded release regressions for profiling, multi-entity generation, and
  validation wall time and peak traced allocations.

### Fixed

- Fixed ISO date columns being misclassified as phone numbers during CSV
  profiling.
- Validation reports now honor all `ValidationSettings` section toggles and
  `fail_fast`, and record the effective settings used.
- Container builds no longer default to version `0.8.1`, and publication now
  rejects image metadata that differs from the package version.
- `GenerationSettings.locale` now controls seeded Faker values, with clear
  rejection of unsupported locales.
- CSV and Trino profiles preserve low-cardinality frequency ranks with
  synthetic labels instead of exposing source category values.
- Incomplete staged generation and review bundles are removed when interactive
  cancellation interrupts writing or validation.
- Mid-write disk exhaustion removes partial staged folder, review, and
  single-entity output without publishing success metadata.
- Interrupted folder publication removes the renamed destination, while
  interrupted single-entity publication restores replaced files and removes
  partial new output.

### Security

- Advisor requests replace singleton categorical values with synthetic labels
  before a provider can receive the profile or baseline specification.
- Documented the public threat model, validation assurance levels, exact-row
  reuse detection limits, and the absence of statistical privacy guarantees.
- Trino SQL access is limited to validated read-only operations and dedicated
  bounded profiling; forbidden and non-allowlisted queries fail before a
  connection while allowlisted metadata and aggregate discovery remain available.
- Python, CLI, and generator MCP generation reject raw-looking sensitive
  categories, unsafe sensitive distributions, and privacy-policy opt-outs before
  creating artifacts or echoing rejected values.
- Masked Trino samples use opaque placeholders for rare free text and
  quasi-identifiers.
- MCP installations exclude the incompatible 2.x SDK until the transport
  migrates to its replacement API.
- JSON dataset inputs are bounded by row count, nested value count, nesting
  depth, and string value length before validation.

[1.0.0rc6]: https://github.com/wa-pis/agent-paranoid-android/compare/v1.0.0rc5...v1.0.0rc6
[1.0.0rc5]: https://github.com/wa-pis/agent-paranoid-android/compare/v1.0.0rc4...v1.0.0rc5
[1.0.0rc4]: https://github.com/wa-pis/agent-paranoid-android/compare/v1.0.0rc3...v1.0.0rc4
[1.0.0rc3]: https://github.com/wa-pis/agent-paranoid-android/compare/v1.0.0rc2...v1.0.0rc3
[1.0.0rc2]: https://github.com/wa-pis/agent-paranoid-android/compare/v1.0.0rc1...v1.0.0rc2
[1.0.0rc1]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.12.0...v1.0.0rc1
