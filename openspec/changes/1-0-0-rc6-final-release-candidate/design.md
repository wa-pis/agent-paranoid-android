# Design: 1-0-0-rc6-final-release-candidate

## Approach

1. Replace the global rare-value map with a deterministic map keyed by entity,
   field, and category index. Generate an opaque field-scoped placeholder and
   reserve every original category value plus every placeholder already in the
   request.
2. Make the structured provider path return a frozen generic result containing
   the parsed model and immutable bounded metadata. Failed calls raise a typed
   contract error carrying the same call-local metadata. Keep the mutable
   `last_run_metadata` assignment only for legacy callers.
3. Parse `TRINO_DEPLOYMENT_PROFILE` in the dependency-free configuration layer.
   `query_work_limits_from_env` rejects an unset cumulative scan ceiling for
   `shared-hardened`; `doctor` reports the profile and effective ceiling after
   the Trino smoke check.
4. Bump active package and user-facing release references to `1.0.0rc6`, add
   the RC6 OpenSpec/checklist/evidence template, and keep RC5 artifacts as
   historical superseded evidence. Stable promotion is allowed only from the
   accepted RC6 tag plus reviewed metadata-only changes.

## Data And Contracts

- `advisor.py`: rare-category replacement map and deterministic placeholder
  contract.
- `providers/openai.py`: `StructuredCompletionResult[T]` and
  `OpenAIAdvisorCallError.metadata`.
- `trino_config.py`: `TrinoDeploymentProfile` and `TRINO_DEPLOYMENT_PROFILE`.
- `trino_work_budget.py`: profile-aware cumulative scan policy.
- `cli_doctor.py`: bounded effective Trino policy status.
- `docs/reference/configuration.md`, README, release docs, roadmap, changelog,
  package metadata, and RC6 OpenSpec files.

## Failure Modes

- A placeholder collision is resolved by a deterministic suffix; no source
  category is silently merged with another category.
- Concurrent provider calls may still update the legacy last-call property in
  either order, but their returned results and raised errors retain their own
  metadata.
- Invalid deployment profiles and missing shared-hardened scan ceilings fail
  closed before the Trino MCP server is launched. Doctor emits only a generic
  capability failure when the policy cannot be loaded.
- Missing attribution, signature/approval URL, public artifact hashes, or
  clean-install evidence leaves RC6 incomplete and blocks stable promotion.

## Alternatives

- Keep a global raw-value replacement map: rejected because equal rare values
  in different fields leak equality and can collide with ordinary categories.
- Remove `last_run_metadata` immediately: rejected because it needlessly breaks
  existing callers; it is retained as an explicitly legacy view.
- Make cumulative scan limits mandatory in every environment: rejected because
  local trusted use has a documented, explicit policy and no provider-wide
  estimate is available without deployment context.
