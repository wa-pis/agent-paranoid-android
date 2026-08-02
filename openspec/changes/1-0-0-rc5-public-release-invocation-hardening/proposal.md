# Change Proposal: 1-0-0-rc5-public-release-invocation-hardening

## Summary

Make `1.0.0rc5` the final public-acceptance and cumulative-resource-hardening
candidate before `1.0.0`. RC5 closes the remaining RC4 release-evidence gap,
separates database-result and transport-response budgets, adds whole-invocation
column/time limits, and makes the default-versus-opt-in MCP documentation
consistent.

## Motivation

The `v1.0.0rc4` tag and GitHub prerelease are not by themselves proof that the
candidate is usable by an external user. Stable promotion requires exact
wheel/sdist publication, public-index installation, README execution, and
attestation evidence from outside the repository checkout.

The first invocation budget also needs a stricter boundary. A database result
can fit its limit while the final MCP JSON response exceeds it after envelopes,
escaping, dictionary conversion, and metadata are added. Per-query limits also
do not bound a wide-table profiling invocation that fans out across many
queries. These limits must be explicit before the stable compatibility promise.

## Scope

In scope:

- Verify or complete public RC4 publication and acceptance for PyPI and GitHub
  artifacts, including clean base and optional-extra environments.
- Split `database_result_bytes` from `transport_response_bytes`; account for
  database bytes during cursor consumption and final transport bytes after MCP
  JSON serialization.
- Return a small reserved error response that is guaranteed to fit when the
  transport response budget is exceeded.
- Add cumulative invocation limits for profiled columns, statements, elapsed
  time, and cumulative estimated scan bytes where the engine exposes a reliable
  estimate.
- Use benchmark-backed defaults and document every application-level limit in
  the configuration reference.
- Align README, MCP examples, configuration, architecture references, and
  OpenSpec wording around default aggregate-only tools versus explicit
  opt-in row-returning tools.
- Repeat all release and public-artifact gates against the exact RC5 commit.

Out of scope:

- New data-generation features, source adapters, or model providers.
- Raising per-query limits to compensate for missing invocation limits.
- Describing `run_safe_select` as source-free, anonymous, PII-free, or
  privacy-safe; it remains a separately enabled row-returning capability.
- Making cumulative scan bytes mandatory where Trino cannot provide a bounded,
  trustworthy estimate.
- Promoting stable before the public RC4/RC5 evidence is complete.

## Safety Impact

The effective transport output is bounded independently of the database fetch
path. A large result cannot evade the budget through JSON expansion. Cumulative
column, statement, and deadline limits reduce fan-out and denial-of-service
risk from one profiling invocation. Error responses are bounded as well.

Default generator and aggregate-only Trino profiling responses remain
metadata-only and source-literal-free. Explicitly enabled `run_safe_select`
remains outside that guarantee; its audit records must stay metadata-only.

## Compatibility

New configuration limits are additive but change failure behavior for requests
that previously ran until per-query limits were reached. Their names, defaults,
units, and error contract must be documented and covered by tests. Existing
CLI, `DatasetSpec`, artifact, and default MCP schemas remain unchanged except
where documentation corrects the default-versus-opt-in wording.

RC5 public artifacts must be identified by exact package version, tag, commit,
checksums, SBOM, provenance, and attestations. Stable promotion may add only a
reviewed version/changelog/release-metadata-only diff to the accepted RC5
source tree.
