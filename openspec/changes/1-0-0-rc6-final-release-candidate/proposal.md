# Change Proposal: 1-0-0-rc6-final-release-candidate

## Summary

Make `1.0.0rc6` the final release candidate before stable promotion. RC6
closes the remaining security and operational findings around rare-category
sanitization, per-call advisor metadata, shared Trino scan policy, and
publicly verifiable review evidence.

## Motivation

The RC5 runtime is bounded, but two edge cases still weaken its contract:
rare-category replacement is global by raw value, and mutable provider metadata
can be attributed to the wrong concurrent call. Shared Trino deployments also
need an explicit fail-closed policy when cumulative scan work is not bounded.

The release process must make RC6, rather than the historical RC5 artifacts,
the single immutable source tree used for stable promotion. Independent review
evidence must be attributable and publicly verifiable without exposing source
data or secrets.

## Scope

In scope:

- Use field-scoped deterministic rare-category placeholders that avoid normal
  category values and other generated placeholders.
- Return typed OpenAI completion values with metadata owned by that invocation,
  including bounded metadata on preflight and provider failures.
- Add `trusted-local` and `shared-hardened` Trino deployment profiles; require
  a finite cumulative estimated-scan limit for `shared-hardened` and show the
  effective policy in `doctor`.
- Bump active package/docs/release state to RC6 and add a separate acceptance
  checklist with attributable review evidence fields.
- Verify public artifacts and all supported installation/container profiles
  from the immutable RC6 tag before stable promotion.

Out of scope:

- New providers, formats, generators, MCP tools, or Pointblank integration.
- Large performance refactors or changes to the existing transport budget
  protocol.
- Treating heuristic profiling or an AI proposal as proof of anonymity or
  domain truth.

## Safety Impact

Rare values are replaced in safe advisor metadata only; source rows and raw
values never enter generated output or provider metadata. Per-call metadata is
bounded and excludes prompts, profile values, credentials, and exception text.
The shared-hardened profile fails closed before Trino MCP startup when total
estimated scan work is unbounded. `trusted-local` is an explicit local policy,
not a production privacy claim.

## Compatibility

`OpenAIAdvisorClient.complete` remains compatible and returns the same payload;
new callers use `complete_with_metadata`. `last_run_metadata` remains only as a
legacy sequential compatibility view. Existing Trino configuration is
compatible under the default `trusted-local` profile; shared deployments must
set the finite cumulative scan limit. CLI, MCP, DatasetSpec, and artifact
schemas remain unchanged apart from the documented doctor status and release
version.
