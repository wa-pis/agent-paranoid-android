# Change Proposal: 1-0-0-rc4-privacy-invocation-hardening

## Summary

Make `1.0.0rc4` a mandatory hardening candidate before `1.0.0`. The candidate
closes the default Trino MCP source-literal exposure, introduces a shared
invocation-level work budget, fixes prerelease installation guidance, and
aligns MCP documentation and release acceptance with the actual safety
boundary.

## Motivation

The RC3 application-boundary refactor is merged, but the release is not ready
for stable promotion. The initial RC4 follow-up removed masked row sampling
from the default registration, but the public helper, compatibility
documentation, and adversarial coverage still need to converge on that
decision. The heuristic masking implementation can return source literals
that are not recognized as sensitive. Per-query limits also do not bound the
total work of one nested profiling invocation. Finally, a plain `pip install`
instruction can resolve a stable package instead of the prerelease being
documented.

These are contract and release-readiness issues, not optional feature work.
They must be resolved and demonstrated against a public RC4 artifact before
the stable compatibility promise begins.

## Scope

In scope:

- Remove `sample_rows_masked` from the RC4 public MCP and Python compatibility
  surfaces. RC4 does not retain a row-sampling diagnostic. A future
  row-returning capability requires a separate OpenSpec change with its own
  allowlists, limits, audit contract, and visible capability status.
- Guarantee that default Trino MCP responses do not return literal source-cell
  values, with adversarial regression tests covering every source column.
- Add a `QueryWorkBudget` shared by all nested operations in one invocation,
  including request, SQL/formula, AST, depth, column, statement, and response
  limits.
- Correct prerelease installation and extras documentation and validate the
  literal README workflow from a clean environment using public RC4 artifacts.
- Reconfirm that Trino is an optional integration: the base wheel and CSV/JSON
  workflow do not require the Trino client, SQL parser, or MCP SDK, while the
  separate `trino` extra owns Trino capability checks.
- Clarify the aggregate-only default MCP contract versus the separately
  opt-in `run_safe_select` contract, and document the atomic-write versus
  crash-durability boundary.
- Run the full release and public-artifact acceptance gates for `1.0.0rc4`.

Out of scope:

- Publishing `1.0.0` before RC4 acceptance.
- Adding new domain-specific generation features or changing the deterministic
  generation model.
- Treating heuristic masking as statistical anonymity, re-identification
  resistance, or a certification of privacy.
- Adding unrestricted SQL, write access, or a default raw-row capability.
- Making fsync a stable-release requirement unless the public durability
  contract explicitly promises crash or power-loss durability.

## Safety Impact

The default aggregate-only Trino MCP contract becomes source-literal-free at
the response boundary rather than relying on field-name heuristics. Read-only
SQL policy, allowlists, and generated-data protections remain unchanged. Shared
budgets reduce denial-of-service risk from fan-out and nested profiling.
`run_safe_select` remains a separate explicit opt-in capability and is not
source-free: its bounded result may contain allowed source values, while its
errors and metadata-only audit records must not contain returned values.

No source rows, raw PII, credentials, or secrets may appear in generated
artifacts, default aggregate-only MCP responses, typed errors, or audit
records. The release tests must exercise direct service calls as well as
transport registration.

## Compatibility

Removing `sample_rows_masked` from the default MCP tool list and public helper
surface is a deliberate safety-breaking change to the RC3 surface and must be
reflected in the MCP golden fixture, OpenSpec baseline, migration notes,
documentation, and release notes. The default aggregate profiling tools retain
their stable schemas unless the privacy fix requires a documented change.
`run_safe_select` has independent enablement and must never be described as a
source-free capability.

Prerelease installation commands become version-selecting commands rather than
floating package installs. CLI, Python, generator MCP, Trino MCP, artifact,
and `DatasetSpec` compatibility remains unchanged outside the reviewed Trino
privacy and budget boundaries. Stable promotion uses the accepted RC4
production source tree plus only a reviewed version, changelog, and release
metadata diff; executable code and dependency changes are not allowed in that
promotion diff.
