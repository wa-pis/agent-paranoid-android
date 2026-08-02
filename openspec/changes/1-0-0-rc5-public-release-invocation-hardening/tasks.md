# Tasks: 1-0-0-rc5-public-release-invocation-hardening

## P1 — Public RC4/RC5 artifact acceptance

- [x] Publish and verify the exact `1.0.0rc4` wheel and sdist on public PyPI,
  or record the exact RC5 replacement candidate if RC4 publication cannot be
  completed without changing the verified source tree.
  Evidence: [RC4 published release](../../../docs/release-evidence-1.0.0rc4.md)
  records matching public PyPI and GitHub Release hashes from verification run
  [#5](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30735097985).
- [ ] Publish a complete GitHub prerelease with checksums, SBOM, provenance,
  and attestations, all bound to the exact tag and commit.
- [ ] Install from public indexes in clean environments and run README
  commands without edits for base, `[trino]`, `[mcp]`, and `[mcp,trino]`.
- [ ] Verify `--version`, `demo`, and `doctor` for each applicable profile;
  record package version, artifact hashes, Python version, and extra profile.
- [ ] Re-run public documentation, container signature, package attestation,
  and upgrade-from-`0.12.0` checks from published artifacts only.

## P2 — Database versus transport response budgets

- [ ] Rename/split the typed budget counters into
  `database_result_bytes` and `transport_response_bytes`.
- [ ] Enforce database-result bytes incrementally during cursor consumption,
  including row conversion overhead needed by the client result boundary.
- [ ] Enforce transport-response bytes after final MCP JSON serialization and
  before stdout/transport write, including envelopes, escaping, dictionaries,
  nested metadata, and error objects.
- [ ] Reserve and test a fixed small error response that always fits the
  transport budget; reject configurations whose limit is below that minimum.
- [ ] Add tests for wide rows, nested metadata, escaping expansion, database
  overflow, transport overflow, and bounded overflow errors.

## P2 — Cumulative invocation limits

- [ ] Add `max_profiled_columns`, `max_invocation_seconds`, and optional
  `max_cumulative_estimated_scan_bytes` to the typed configuration and budget.
- [ ] Start with defaults of 100 profiled columns, 150 statements, and 120
  seconds; either retain them with benchmark evidence or document justified
  alternatives. Do not use 1000 columns or 2048 statements without evidence.
- [ ] Enforce column, statement, deadline, and scan limits across nested table
  profiling with one shared monotonic budget; no helper may reset or restore
  consumed work.
- [ ] Document environment names, defaults, units, per-query versus
  per-invocation scope, and failure behavior in configuration reference.
- [ ] Add wide-table, statement-fan-out, timeout, concurrency-isolation, and
  preflight/no-connection tests.

## P3 — MCP documentation contract

- [ ] Update README, MCP examples, MCP how-to, AI integration, configuration,
  application-boundary references, diagrams, and canonical OpenSpec wording.
- [ ] Use the terms `default aggregate-only tools` and `explicit opt-in
  row-returning tools` consistently. Narrow all server-wide claims that imply
  every MCP response is source-free.
- [ ] Add a documentation test that rejects stale `sample_rows_masked` names
  and broad source-free/privacy-safe claims around `run_safe_select`.

## Release gates

- [ ] Run `python3 -m ruff check src tests scripts`.
- [ ] Run `python3 -m compileall -q src tests scripts`.
- [ ] Run `python3 -m pytest --cov=test_data_agent --cov-report=term-missing --cov-fail-under=85`.
- [ ] Run `scripts/check_release.sh` and `mkdocs build --strict`.
- [ ] Confirm the public artifact evidence is attached to the exact RC5 tag
  and that stable promotion has only the allowed release-metadata diff.
