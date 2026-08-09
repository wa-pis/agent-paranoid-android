# Change Proposal: 1-0-0-rc6-final-release-candidate

## Summary

Make `1.0.0rc6` the final release candidate before stable promotion. RC6
tracks and closes the remaining security and operational findings around
rare-category sanitization, provider failure redaction, per-call advisor
metadata, shared Trino scan policy, and publicly verifiable review evidence.

## Motivation

The RC5 runtime is bounded, but two edge cases still weaken its contract:
rare-category replacement is global by raw value, and mutable provider metadata
can be attributed to the wrong concurrent call. Shared Trino deployments also
need an explicit fail-closed policy when cumulative scan work is not bounded.

The release process must make RC6, rather than the historical RC5 artifacts,
the single immutable source tree used for stable promotion. Independent review
evidence must be attributable and publicly verifiable without exposing source
data or secrets.

The independent review of commit
`29afe41b574e5e6ffe0570ac5f8cbd4447b2f90b` found follow-up work after the
initial RC6 hardening. PR #331 suppresses provider text from normal formatted
tracebacks but still retains the original exception in Python `__context__`;
PR #332 reserves placeholder-shaped baseline literals but does not sanitize a
rare value when baseline categories are reordered. These are RC6 acceptance
work, not post-1.0 deferrals.

PRs #333 through #335 close the raw incomplete-status case, detach the handled
provider exception chains, and fix reordered-baseline placeholder provenance.
The independent exact-tree follow-up for merge `5b3ad7f` found two residuals
within the existing RC6-S2/S3 failure-redaction invariant: ordinary SDK
constructor exceptions outside `OpenAIError` still escape unchanged, and the
provider-call error message still incorporates a dynamic Python exception class
name. Both remain RC6 acceptance work; they do not create new finding IDs.

The repository-wide security review of the current RC6 worktree found further
release-blocking gaps: common categorical values can cross the external advisor
boundary, sensitive numeric Trino aggregates can reveal exact source values,
provider constraints can inject literals into generated rows, generator MCP
stdio input is not framed before parsing, and the release workflow does not
cryptographically bind publication to an accepted source tree. These findings
are added to RC6 because `v1.0.0rc6` has not yet been tagged or accepted.

The same RC6 scope now includes the deployment-conditional and lower-confidence
follow-ups from that review. They are acceptance requirements, not a deferred
RC7 backlog: active-request exhaustion, backend error and metadata redaction,
the explicit row-returning opt-in surface, semantic-provider execution and
output policy, filesystem race resistance, publication/overwrite semantics,
terminal and log escaping, and evidence for external repository and PyPI
release controls.

## Scope

In scope:

- Use field-scoped deterministic rare-category placeholders that avoid normal
  category values and other generated placeholders, remain independent of
  baseline category order, and leave no original rare value in the provider
  request.
- Make every categorical value crossing an external advisor boundary synthetic
  or otherwise non-reversible; heuristic PII detection is not sufficient as a
  source-free guarantee.
- Suppress exact extrema and percentiles for sensitive numeric Trino columns,
  including values that can be exact for singleton or narrow populations.
- Validate provider-added DatasetSpec constraints before persistence and again
  before publication; formulas may use only allowlisted numeric arithmetic and
  may not inject string literals or target sensitive fields.
- Apply a privacy/type check after constraint solving and keep formula,
  validation, and semantic-provider failures bounded and source-free.
- Give generator MCP the same pre-parse raw-frame, per-invocation, and final
  response bounds as the Trino MCP; enforce structural JSON limits before full
  object materialization where practical.
- Harden artifact-name validation and neutralize spreadsheet formula markers
  at the CSV export boundary.
- Bound active MCP requests and shared Trino concurrency, release request state
  on every terminal path, and return fixed errors when capacity is exhausted.
- Keep Trino driver failures and catalog/schema enumeration policy behind a
  bounded MCP error boundary; document the metadata exposure decision.
- Define a separate privacy contract for opt-in `run_safe_select`, including
  a tested policy for strings that heuristic masking cannot classify.
- Bound semantic-provider time, cancellation, and replay behavior; require
  synthetic-only names/addresses and post-generation privacy/type validation.
- Make filesystem publication and overwrite operations resistant to symlink
  and TOCTOU races, define completion/read-validation semantics, and require
  explicit approval for sibling-artifact replacement.
- Escape untrusted CLI/log metadata and record deployed branch/tag ruleset,
  required-check, and PyPI Trusted Publisher evidence.
- Make CI change classification and release publication depend on trusted
  code, signed immutable tags, an accepted commit digest, and a machine-
  readable RC acceptance manifest.
- Return typed OpenAI completion values with metadata owned by that invocation,
  including bounded metadata on preflight and provider failures.
- Convert every ordinary SDK initialization exception, transport, provider,
  incomplete-response, and structured-validation failure to fixed bounded
  advisor errors without retaining provider exceptions in `__cause__` or
  `__context__`, reflecting provider-controlled status text, or incorporating
  dynamic Python exception class names.
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
- Differential privacy, k-anonymity, and formal statistical disclosure
  guarantees beyond the source-free provider and artifact boundary.

## Safety Impact

Rare values are replaced in safe advisor metadata only; source rows and raw
values never enter generated output or provider metadata, including when the
profile and baseline use different category order. Per-call metadata and public
errors are bounded and exclude prompts, profile values, credentials, provider
status text, and retained exception objects.
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
