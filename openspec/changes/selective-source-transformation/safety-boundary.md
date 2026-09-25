# Selective Transformation Safety Boundary — Local Operator Decision

This document proposes a scoped amendment, not an active exception to AGENTS.md.
Do not enable source-preserving execution until this boundary, matching baseline
specifications and executable safety checks have received independent review.

## Development Before Activation

The owner approved separating development from activation on 2026-09-25.
Private implementation and isolated executable tests on fictional inputs may
precede the final implementation safety review. Use bounded temporary test
outputs, no user destinations, real databases, production data or external APIs.
Keep public CLI/Python/MCP execution unavailable. Tests must exercise the actual
private implementation, not monkeypatch product safeguards to obtain a pass.

The sequence is implementation with failing/passing tests, end-to-end safety
evidence, independent review of the exact implementation SHA, then separately
gated activation and release. Existing preservation, classification, receipt,
snapshot, privacy and publication requirements still govern the implementation.
No dataset is authorized by this development permission. Documentation changes
do not override workspace/tool restrictions or establish that prior tool
rejections have been lifted; a remaining tool restriction must be reported,
not bypassed through another path.

## Separate Surface

Existing generate/profile/advisor/MCP workflows remain source-free as documented.
Neither a valid behavior policy nor a loaded mapping enables preservation there.
The new explicitly selected transformation surface produces a mixed-origin,
one-to-one transformed dataset, never a certified anonymous or fully synthetic one.

## Preservation Authority

On 2026-09-24 the user approved the product requirement that the human personally
confirms concrete columns and the exact plan before execution; the agent cannot
grant itself permission, and sensitive or disputed columns remain blocked.
The user subsequently selected trust in the local CLI operator as the deployment
boundary. This is not a cryptographic proof of human identity: a process with
the same local filesystem and terminal privileges can impersonate the operator.
That equal-privilege impersonation is explicitly outside this deployment's
protection claim. No source-bearing dataset was approved by this conversation.

Every input field requires an explicit action. Only fields explicitly declared
non-sensitive and authorized for preservation may carry original logical values.
Unresolved sensitive/unknown classifications or conflicting profiling evidence
block preservation, including unmatched-value preserve fallback. Agent proposals,
heuristic output, arbitrary authorization-reference strings and bulk acceptance
cannot grant or expand this authority. Sensitive fields require replacement or
exclusion; merely relabeling them does not declassify them.

DECIMAL preservation is blocked by default, including an unmatched-value
preserve fallback, even when the profile has no positive sensitivity flag.
The proposed narrow human exception is not active: current profile evidence
does not identify whether a positive numeric signal came solely from a
false-positive shape or from card/phone/semantic evidence. No exception may
be enabled until that provenance is typed, snapshot-bound, tested and
independently reviewed. Source-free DECIMAL generation keeps its existing
privacy checks.

The execution boundary must verify approval of the exact reviewed plan and
fixed input snapshots. Private receipt helpers are not a completed execution
boundary; the selection below is not permission to trust a boolean or opaque
reference.

### Selected Approval Transport: Trusted Local Operator

The existing `agent-approve` spec hash selects a source-free generation plan; it
is not transformation approval. The new, separate local CLI approval must:

- present a bounded, value-free review of the exact effective plan in the local
  terminal: input/plan identity, every field action including unmatched-preserve
  fallbacks, the proposed preserved columns, and each column's reviewed
  sensitivity/conflict status. A digest alone is not sufficient for confirmation;
- require a fresh explicit interactive terminal confirmation, not a CLI flag,
  environment variable, piped stdin, or caller-supplied `authorization_ref`;
- bind the resulting restricted receipt to that displayed review, its immutable
  sensitivity/classification evidence, the reviewed policy, fixed source bytes
  and all referenced mapping/generation-policy bytes. Revalidate the evidence
  against those same snapshots and consume them at execution; a changed input
  or classification requires review and approval again;
- keep default MCP and agent planning/advice unable to create or broaden that
  receipt. No agent/MCP transformation-approval endpoint may mint a receipt.
  Noninteractive/agent execution may only consume an existing matching receipt,
  never replace local approval;
- keep sensitive, unknown and conflicting preservation prohibited regardless
  of operator confirmation.

The receipt is an exact-input integrity record, not a signature or proof of
personhood. Owner-only local storage and an interactive prompt prevent accidental
or remote approval through supported interfaces; they do not protect against an
agent/process with equivalent local privileges. A separately controlled signing
authority is not selected or implemented. This boundary must receive matching
AGENTS.md/baseline-spec amendments, executable tests and independent safety
review before source-preserving execution is enabled.

## Identity And Execution

Approval binds source bytes/supported fixed snapshots, policy, referenced mapping
bytes and generation policies, including transitive inputs. A column-schema hash
alone is insufficient. Validate and consume the same snapshots; changed inputs
require renewed review. Budgets apply across the invocation, not per helper.
SQL reads remain separately authorized, read-only, allowlisted and bounded.

Copying original values is allowed only in explicitly permitted preserved output
fields. This does not prohibit independently synthesized equality for approved
zero/declared-rounding cases or independently recomputed derived values that
coincide with originals. Those cases never permit skipping replacement/computation
or falling back to copying; the financial replacement contract still applies.
Mappings may contain private originals locally; mapping output values must still
pass applicable privacy/type/constraint checks. One-to-one row correspondence is
internal and must not become an exported original-to-replacement lookup table.
All derived values and relationships must validate before atomic publication.
Failures must not publish a partial dataset or fall back to copying source values.

## Restricted And Public Artifacts

Source-bearing policies, maps, snapshots and identity evidence are restricted
local inputs. Never send them to providers, logs, exception chains or default MCP
responses. Public summaries contain bounded counts/status and opaque references,
not literals. Output manifests must state mixed origin and residual privacy risk.
Preserved combinations can still identify people or reveal confidential facts;
successful validation does not prove anonymity.

## Required Executable Evidence

- Default source-free surfaces cannot invoke preservation through forged settings.
- Unknown/new fields and schema drift fail before execution.
- Sensitive/unknown/conflicting preservation fails, including fallback and agent use.
- Approval cannot be fabricated by setting authorization_ref or reusing stale hashes.
- Source/policy/mapping mutations invalidate approval; no check-then-reopen path.
- Restricted values do not leak through errors, warnings, summaries or providers.
- Mapping collisions, invalid formulas, resource exhaustion and privacy failures
  prevent publication and preserve existing destination artifacts.
- Fictional end-to-end finance data retains authorized reference combinations,
  changes amounts, recomputes totals and preserves declared key relationships.
- Zero/declared-rounding equality and coincident computed totals are accepted only
  through the declared synthesis/derivation path, never a copy/skip fallback.

The existing helper tests cover only parts of these requirements. No task above
is considered passed merely because isolated parsers or loaders passed review.
