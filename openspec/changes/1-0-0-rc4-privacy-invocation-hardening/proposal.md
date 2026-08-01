# Change Proposal: 1-0-0-rc4-privacy-invocation-hardening

## Summary

Make `1.0.0rc4` a mandatory hardening candidate before `1.0.0`. The candidate
closes the default Trino MCP source-literal exposure, introduces a shared
invocation-level work budget, fixes prerelease installation guidance, and
aligns MCP documentation and release acceptance with the actual safety
boundary.

## Motivation

The RC3 application-boundary refactor is merged, but the release is not ready
for stable promotion. The default Trino MCP registration still includes a
masked row-sampling capability whose heuristic masking can return source
literals that are not recognized as sensitive. Per-query limits also do not
bound the total work of one nested profiling invocation. Finally, a plain
`pip install` instruction can resolve a stable package instead of the
prerelease being documented.

These are contract and release-readiness issues, not optional feature work.
They must be resolved and demonstrated against a public RC4 artifact before
the stable compatibility promise begins.

## Scope

In scope:

- Remove row sampling from the default Trino MCP surface, or move it behind an
  explicit, separately named, operator-enabled, reviewed, and audited opt-in
  boundary.
- Guarantee that default Trino MCP responses do not return literal source-cell
  values, with adversarial regression tests covering every source column.
- Add a `QueryWorkBudget` shared by all nested operations in one invocation,
  including request, SQL/formula, AST, depth, column, statement, and response
  limits.
- Correct prerelease installation and extras documentation and validate the
  literal README workflow from a clean environment using public RC4 artifacts.
- Clarify aggregate-only versus row-returning MCP contracts and document the
  atomic-write versus crash-durability boundary.
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

The default Trino MCP contract becomes source-literal-free at the response
boundary rather than relying on field-name heuristics. Read-only SQL policy,
allowlists, and generated-data protections remain unchanged. Shared budgets
reduce denial-of-service risk from fan-out and nested profiling. Row-returning
diagnostics, if retained, are clearly opt-in and receive a separate safety and
audit treatment.

No source rows, raw PII, credentials, or secrets may appear in generated
artifacts, MCP responses, error messages, or audit records. The release tests
must exercise direct service calls as well as transport registration.

## Compatibility

Removing `sample_rows_masked` from the default MCP tool list is a deliberate
safety-breaking change to the RC3 surface and must be reflected in the MCP
golden fixture, OpenSpec baseline, migration notes, and release notes. The
default aggregate profiling tools retain their stable schemas unless the
privacy fix requires a documented change. `run_safe_select` remains explicit
operator opt-in and must not be described as a source-free capability.

Prerelease installation commands become version-selecting commands rather than
floating package installs. CLI, Python, generator MCP, Trino MCP, artifact,
and `DatasetSpec` compatibility remains unchanged outside the reviewed Trino
privacy and budget boundaries.
