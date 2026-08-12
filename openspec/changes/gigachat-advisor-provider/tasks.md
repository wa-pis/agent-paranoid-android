# Tasks: gigachat-advisor-provider

Do not start implementation until this OpenSpec is accepted. Normal tests and
release gates must not make live or paid GigaChat calls.

## Contract And Dependency Gate

- [x] Record the proposal, design, and affected capability deltas.
- [x] Verify the official `gigachat` SDK license, transitive dependencies,
  release activity, structured-output API, and Python 3.11-3.14 compatibility.
- [x] Select and document a bounded dependency range only if the SDK passes the
  base, `gigachat`, and `all` installation matrices.
- [x] Define frozen typed settings, scope/authentication modes, run metadata,
  stable error categories, and an injected SDK protocol.
- [x] Confirm the provider-neutral `AdvisorExchange` and artifact schemas need
  no breaking change; version any unavoidable serialized change.

## Provider Adapter

- [x] Implement an optional `GigaChatAdvisorClient` without importing the SDK
  from the package root or deterministic core.
- [x] Enforce official endpoints, mandatory TLS verification, optional CA
  bundle validation, and mutually exclusive environment-based auth modes.
- [x] Map trusted instructions and untrusted exchange JSON into separate
  messages for one non-streaming strict-schema completion.
- [x] Enforce request, response, output-token, timeout, retry, usage, and total
  invocation budgets.
- [x] Reject abnormal finish reasons, multiple or missing choices, oversized
  content, malformed JSON, extra data, and schema-invalid proposals.
- [x] Convert provider and SDK failures to fixed redacted errors and per-call
  bounded metadata without retaining raw requests or responses.
- [x] Reuse the existing fingerprint, safety, review, and local field-label
  restoration boundaries without giving the adapter persistence authority.

## CLI And Packaging

- [x] Add the optional `gigachat` extra and include it in `all` only after the
  dependency gates pass.
- [x] Add `gigachat` to the existing `agent-advise --provider` choice while
  preserving all existing defaults and JSON contracts.
- [x] Resolve credentials only from runtime environment or injected secret
  input; do not add credential-bearing CLI flags or config artifacts.
- [x] Add a local-only `doctor --require-extra gigachat` capability smoke with
  fake transport, no credential resolution, and no network access.
- [x] Keep missing-extra, missing-secret, invalid-scope, and TLS failures
  bounded, redacted, and free of tracebacks.

## Safety And Regression Tests

- [x] Add fake-SDK unit tests for request roles, strict schema, settings,
  response parsing, finish reasons, retries, cancellation, and cleanup.
- [x] Inspect the final outbound request for source-row, PII, credential,
  token, locally preserved value, and categorical-predicate sentinels.
- [x] Prove invalid or provider-filtered output cannot change the workspace,
  persist a review, approve a spec, or generate records.
- [x] Prove a valid proposal remains fingerprint-bound, review-gated, and uses
  the existing deterministic generator after approval.
- [x] Add isolated-wheel tests for base, `gigachat`, and `all` profiles across
  Python 3.11-3.14 without a live provider.
- [x] Add minimum/latest dependency, license, secret-scan, and import-boundary
  coverage for the new extra.

## Documentation And Release

- [x] Update README, installation, configuration, advisor, CLI, doctor,
  privacy, support-policy, implementation-map, and troubleshooting docs.
- [x] Add a runnable synthetic GigaChat example with placeholder credentials,
  supported scopes, CA-bundle guidance, review/approval steps, and cost notice.
- [x] Document that external GigaChat receives safe metadata, not source rows
  or exact locally preserved values, and that TLS verification cannot be
  disabled.
- [x] Update changelog, roadmap, public stability map, and release checklist
  for an experimental additive provider.
- [x] Run ruff, mypy, compile, focused and full pytest, strict docs build,
  package build, dependency/license checks, isolated-wheel installs, and
  synthetic CLI/doctor smokes on exact implementation tip
  `f7fc12b97a7ebeae79bd83f9b82aa41ea588d4c3` from PR #404.
- [ ] Put the implementation through a new minor release candidate because it
  changes runtime behavior, dependencies, public CLI, and a security boundary.
