# Design: 1-0-0-rc6-final-release-candidate

## Approach

1. Resolve privacy policy by field and destination. Preserve source categories
   locally only for fields explicitly allowlisted as bounded non-sensitive
   business enums. Content-based PII, secret, identifier, and free-text checks
   remain fail-closed. Provider-bound categories always use synthetic labels,
   and Trino/MCP aggregate disclosure additionally requires table and column
   allowlists. For transformed fields, build a deterministic map scoped by
   entity and field, reserve original and generated labels, and verify provider
   payloads contain no original literals.
2. Make the structured provider path return a frozen generic result containing
   the parsed model and immutable bounded metadata. Failed calls raise a typed
   contract error carrying the same call-local metadata. Keep the mutable
   `last_run_metadata` assignment only for legacy callers.
3. Catch every ordinary exception at SDK client construction, retain only a
   local failure flag, and raise the fixed local `ValueError` after leaving the
   active `except` scope. Translate provider and validation failures at the
   same detached boundary so public errors retain neither `__cause__` nor
   `__context__`. Use exact fixed allowlisted text; do not interpolate raw
   response status, provider exception text, or dynamic Python exception class
   names.
4. Parse `TRINO_DEPLOYMENT_PROFILE` in the dependency-free configuration layer.
   `query_work_limits_from_env` rejects an unset cumulative scan ceiling for
   `shared-hardened`; `doctor` reports the profile and effective ceiling after
   the Trino smoke check.
5. Bump active package and user-facing release references to `1.0.0rc6`, add
   the RC6 OpenSpec/checklist/evidence template, and keep RC5 artifacts as
   historical superseded evidence. Stable promotion is allowed only from the
   accepted RC6 tag plus reviewed metadata-only changes.
6. Treat all categorical values as source-derived metadata at the external
   provider boundary. Replace them with field-scoped synthetic labels/ranks
   before building the request; do not use heuristic PII classification as the
   final egress decision. Sensitive numeric profiles expose only bounded shape
   summaries, never exact extrema or percentiles.
7. Validate advisor-proposed constraints against the target field type and an
   allowlisted numeric expression grammar. Reject string constants and
   sensitive targets, then run privacy and type validation after constraint
   solving and before any artifact is committed.
8. Reuse the bounded Trino stdio framing and final-response writer for the
   generator MCP, with a fresh non-resettable invocation budget. Add parser
   limits for JSON node/depth/container work before materializing untrusted
   profile/spec payloads.
9. Make artifact names single safe path components, neutralize formula-prefixed
   CSV cells, and convert expression/validation diagnostics to fixed local
   reasons. Load CI classifiers from trusted code and require a signed tag,
   accepted commit digest, and machine-readable RC acceptance manifest before
   release publication.
10. Replace the unbounded active-request map with bounded admission control
    shared by the MCP and Trino execution paths. Every request must release its
    slot and state on success, error, cancellation, disconnect, timeout, and
    teardown; exhaustion returns a fixed local error.
11. Keep Trino driver failures and backend enumeration behind a fixed bounded
    error boundary. Make the `run_safe_select` opt-in contract explicit and
    independently enforce row privacy rather than treating heuristic masking as
    a guarantee. Define the allowed catalog/schema metadata surface.
12. Treat semantic providers as untrusted execution and output boundaries:
    enforce timeout/cancellation, deterministic replay or fingerprinting for a
    seed, synthetic-only identity outputs, and post-generation privacy/type
    checks. Centralize filesystem publication policy with no-follow and inode
    validation, define single-entity completion and sibling-overwrite approval,
    and escape untrusted CLI/log metadata. Record external release-control
    evidence alongside the source-tree checks.

## Data And Contracts

- `advisor.py`: order-independent rare-category replacement map, deterministic
  placeholder contract, and sanitization-completeness postcondition.
- `profiling/distribution_profiler.py`, `advisor.py`, and provider adapters:
  source-free categorical advisor payloads and provider-boundary evidence.
- `trino_masking.py`, `trino_query_builders.py`, and legacy profile adapters:
  suppression of exact sensitive numeric aggregates.
- `core/constraint.py`, `rules/expressions.py`, `advisor.py`,
  `generation/constraint_solver.py`, and validation: provider proposal formula
  contract and post-solve privacy/type enforcement.
- `mcp_generator_transport.py`, `mcp_generator_server.py`, and JSON adapters:
  bounded generator MCP framing and pre-materialization input limits.
- `io/artifacts.py`, `io/writers.py`, and validation presenters: safe artifact
  names, CSV formula neutralization, and bounded diagnostics.
- `mcp_trino_transport.py`, `trino_client.py`, `mcp_trino_server.py`, and
  catalog/schema discovery: bounded active-request admission, fixed backend
  errors, and explicit opt-in row/metadata policy.
- `providers/semantic_provider.py`, `generation/entity_generator.py`, and
  provider contracts: timeout/cancellation, deterministic replay, synthetic
  identity output, and post-generation privacy/type checks.
- `workspace_store.py`, `io/workflows.py`, `io/writers.py`, and
  `io/artifacts.py`: centralized no-follow filesystem publication, TOCTOU
  validation, completion markers, and explicit bundle overwrite policy.
- `cli_presenter.py` and CLI/logging adapters: escaped and bounded untrusted
  metadata output.
- `agent_advising.py`: persisted-review verification that distinguishes a
  request-generated placeholder from an ordinary placeholder-shaped literal
  without relying on category position alone.
- `providers/openai.py`: `StructuredCompletionResult[T]` and
  `OpenAIAdvisorCallError.metadata`, fixed bounded failure reasons for every
  ordinary SDK exception, and dropped provider exception chains.
- `trino_config.py`: `TrinoDeploymentProfile` and `TRINO_DEPLOYMENT_PROFILE`.
- `trino_work_budget.py`: profile-aware cumulative scan policy.
- `cli_doctor.py`: bounded effective Trino policy status.
- `docs/reference/configuration.md`, README, release docs, roadmap, changelog,
  package metadata, and RC6 OpenSpec files.

## Failure Modes

- A placeholder collision is resolved by a deterministic suffix; no source
  category selected for transformation is silently merged with another
  category. An explicitly allowlisted local business enum is preserved by
  policy rather than relabeled.
- Reordering categories in the baseline does not change which rare values are
  sanitized and cannot leave a raw rare value in the serialized advisor
  request.
- A string that merely matches the placeholder syntax is ordinary untrusted
  data unless request-bound evidence proves it was generated by this sanitizer.
- Provider failures expose neither provider text, dynamic exception class
  names, nor a retained cause/context; incomplete responses use an allowlisted
  local status label.
- Concurrent provider calls may still update the legacy last-call property in
  either order, but their returned results and raised errors retain their own
  metadata.
- Invalid deployment profiles and missing shared-hardened scan ceilings fail
  closed before the Trino MCP server is launched. Doctor emits only a generic
  capability failure when the policy cannot be loaded.
- Missing attribution, signature/approval URL, public artifact hashes, or
  clean-install evidence leaves RC6 incomplete and blocks stable promotion.
- Unresolved source-free, provider-constraint, transport, request-admission,
  provider-output, filesystem, diagnostic-output, or release-identity findings
  leave RC6 incomplete; deployment-conditional findings require recorded
  external evidence rather than documentation-only deferral.

## Alternatives

- Keep a global raw-value replacement map: rejected because equal rare values
  in different fields leak equality and can collide with ordinary categories.
- Reuse profile category indexes against the baseline: rejected because valid
  baselines may reorder categories and silently bypass replacement.
- Use `raise ... from None` inside the provider `except` block: rejected because
  it hides formatted context but still retains the original exception object in
  `__context__`.
- Remove `last_run_metadata` immediately: rejected because it needlessly breaks
  existing callers; it is retained as an explicitly legacy view.
- Make cumulative scan limits mandatory in every environment: rejected because
  local trusted use has a documented, explicit policy and no provider-wide
  estimate is available without deployment context.
