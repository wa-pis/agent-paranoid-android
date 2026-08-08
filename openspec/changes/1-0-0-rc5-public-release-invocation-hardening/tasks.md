# Tasks: 1-0-0-rc5-public-release-invocation-hardening

## P1 — Public RC4/RC5 artifact acceptance

- [x] Publish and verify the exact `1.0.0rc4` wheel and sdist on public PyPI,
  or record the exact RC5 replacement candidate if RC4 publication cannot be
  completed without changing the verified source tree.
  Evidence: [RC4 published release](../../../docs/release-evidence-1.0.0rc4.md)
  records matching public PyPI and GitHub Release hashes from verification run
  [#5](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30735097985).
- [x] Publish a complete GitHub prerelease with checksums, SBOM, provenance,
  and attestations, all bound to the exact tag and commit.
  Evidence: [Release #16](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30734941005)
  published `v1.0.0rc4` from commit `33073c0` and the independent
  [verification run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30735097985)
  validated checksums, SBOM, provenance, and tag-bound attestations.
- [x] Install from public indexes in clean environments and run README
  commands without edits for base, `[trino]`, `[mcp]`, and `[mcp,trino]`.
  Evidence: [Verify Published Release #7](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30736848757)
  installed the exact public RC4 wheel for all four profiles without a source
  checkout and passed the literal README `doctor` and `demo` commands.
- [x] Verify `--version`, `demo`, and `doctor` for each applicable profile;
  record package version, artifact hashes, Python version, and extra profile.
  Evidence: [Verify Published Release #8](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30737685272)
  passed all seven public install profiles and recorded the exact version,
  wheel hash, Python version, and profile in each job summary; its package job
  reverified the wheel, source-distribution, and SBOM hashes.
- [x] Extend the public wheel matrix to `[parquet]`, `[openai]`, and `[all]`;
  verify the CLI, generator-MCP, and Trino-MCP images in the separate
  container matrix.
  Evidence: [Verify Published Release #8](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30737685272)
  passed all three added public wheel profiles and the three separate
  published-image container jobs.
- [x] Re-run public documentation, container signature, package attestation,
  and upgrade-from-`0.12.0` checks from published artifacts only.
  Evidence: [Verify Published Release #9](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30738435369)
  passed from workflow commit `92a4e1a` against immutable tag `v1.0.0rc4` and
  release commit `33073c0`.

## P2 — Database versus transport response budgets

- [x] Rename/split the typed budget counters into
  `database_result_bytes` and `transport_response_bytes`.
- [x] Enforce database-result bytes incrementally during cursor consumption,
  including row conversion overhead needed by the client result boundary.
- [x] Enforce transport-response bytes after final MCP JSON serialization and
  at the production writer boundary before stdout/transport framing is
  emitted, including the complete UTF-8 JSON-RPC envelope, request ID,
  framing, escaping, dictionaries, nested metadata, and error objects.
- [x] Bound JSON-RPC request IDs, including long, Unicode, and escaped IDs, so
  success and overflow responses cannot expand beyond the configured budget.
- [x] Reserve and test a fixed small error response that always fits the
  transport budget; reject configurations whose limit is below that minimum.
- [x] Add tests for wide rows, nested metadata, escaping expansion, database
  overflow, transport overflow, and bounded overflow errors.

## P2 — Cumulative invocation limits

- [x] Add `max_profiled_columns`, `max_invocation_seconds`, and optional
  `max_cumulative_estimated_scan_bytes` to the typed configuration and budget.
- [x] Start with defaults of 100 profiled columns, 150 statements, and 120
  seconds; either retain them with benchmark evidence or document justified
  alternatives. Do not use 1000 columns or 2048 statements without evidence.
  Evidence: [invocation-default benchmark](benchmark-evidence.md) exercises a
  representative 100-column aggregate-only profile in 122 statements.
- [x] Enforce column, statement, deadline, and scan limits across nested table
  profiling with one shared monotonic budget; no helper may reset or restore
  consumed work.
- [x] Propagate remaining invocation time into query timeouts and cancel or
  close an active cursor/connection when the deadline expires.
- [x] Document environment names, defaults, units, per-query versus
  per-invocation scope, and failure behavior in configuration reference.
- [x] Add a wide-table cumulative column-limit test.
- [x] Add statement-fan-out, timeout, concurrency-isolation, and
  preflight/no-connection tests.
  Evidence: `test_nested_profile_budget_stops_before_later_column_connection`,
  `test_client_closes_active_query_when_invocation_deadline_expires`,
  `test_invocation_wrapper_isolates_concurrent_budgets`, and
  `test_client_rejects_statement_budget_before_opening_connection`.

## P3 — MCP documentation contract

- [ ] Update README, MCP examples, MCP how-to, AI integration, configuration,
  application-boundary references, diagrams, and canonical OpenSpec wording.
- [ ] Use the terms `default aggregate-only tools` and `explicit opt-in
  row-returning tools` consistently. Narrow all server-wide claims that imply
  every MCP response is source-free.
- [ ] Add a documentation test that rejects stale `sample_rows_masked` names
  and broad source-free/privacy-safe claims around `run_safe_select`.

## P1 — Agent throughput and local profiling

- [ ] Change review-first folder planning to `cache_mode=auto` by default and
  replace the opt-in `--use-cache` UX with an explicit `--no-cache` refresh
  escape hatch. Preserve metadata-only cache contents and source fingerprint
  invalidation tests.
- [ ] Remove the avoidable two-pass CSV-folder profile where practical by
  retaining a bounded relationship/rule sample during schema streaming.
- [ ] Add typed local profiling budgets for deadline, sample rows, and any
  applicable input byte/cell work; fail closed before publishing partial cache
  metadata and document the defaults.

## P1 — Advisor performance and relationship assistance

- [ ] Add typed advisor settings for model, reasoning effort, complete prompt
  bytes/tokens, output tokens, timeout, retries, and optional service tier.
  Keep provider credentials and prompts out of persisted diagnostics.
- [ ] Add fast/normal/quality presets and benchmark them on representative
  synthetic profiles for proposal validity, safety-preservation rate, latency,
  input/output tokens, retries, and cost before selecting defaults.
- [ ] Make the complete provider request budget include trusted instructions,
  structured-output/schema overhead, and serialization—not only
  `AdvisorRequest.model_dump_json()`.
- [ ] Record bounded non-sensitive advisor run metadata: model, settings,
  request/response sizes, latency, status, retry count, and provider usage.
- [ ] Implement the optional relationship-candidate ranking adapter using the
  existing provider-neutral contract; keep deterministic candidate identity,
  no source rows/raw values, human review, and no direct DatasetSpec mutation.
- [ ] Add tests for cache reuse/refresh, local deadline/sample exhaustion,
  complete advisor budget rejection before network, bounded timeout/retry,
  redacted metrics, and candidate-identity tampering.

## Release gates

- [ ] Run `python3 -m ruff check src tests scripts`.
- [ ] Run `python3 -m compileall -q src tests scripts`.
- [ ] Run `python3 -m pytest --cov=test_data_agent --cov-report=term-missing --cov-fail-under=85`.
- [ ] Run `scripts/check_release.sh` and `mkdocs build --strict`.
- [ ] Run the representative throughput benchmark and attach its results to
  the RC5 release evidence; no performance default is accepted without the
  corresponding latency/safety/quality measurements.
- [ ] Confirm the public artifact evidence is attached to the exact RC5 tag
  and that stable promotion has only the allowed release-metadata diff.
