# Selective Transformation Safety Boundary — Review Draft

This document proposes a scoped amendment, not an active exception to AGENTS.md.
Do not enable source-preserving execution until this boundary, matching baseline
specifications and executable safety checks have received independent review.

## Separate Surface

Existing generate/profile/advisor/MCP workflows remain source-free as documented.
Neither a valid behavior policy nor a loaded mapping enables preservation there.
The new explicitly selected transformation surface produces a mixed-origin,
one-to-one transformed dataset, never a certified anonymous or fully synthetic one.

## Preservation Authority

On 2026-09-24 the user approved the product requirement that the human personally
confirms concrete columns and the exact plan before execution; the agent cannot
grant itself permission, and sensitive or disputed columns remain blocked.
This approves the requirement, not an implemented transport or a claim that a
local prompt proves human identity. The deployment alternatives below still
need to satisfy that requirement; do not silently assume equal-privilege agents
are excluded from the threat model. No source-bearing dataset was approved by
this conversation.

Every input field requires an explicit action. Only fields explicitly declared
non-sensitive and authorized for preservation may carry original logical values.
Unresolved sensitive/unknown classifications or conflicting profiling evidence
block preservation, including unmatched-value preserve fallback. Agent proposals,
heuristic output, arbitrary authorization-reference strings and bulk acceptance
cannot grant or expand this authority. Sensitive fields require replacement or
exclusion; merely relabeling them does not declassify them.

The execution boundary must independently verify the local user's approval of
the exact reviewed plan. The transport and verifiable representation of that
approval still require specification; no current internal model implements it.
This is a release blocker, not permission to trust a boolean or opaque reference.

### Approval Transport Decision Pending

The existing agent approval service checks a caller-supplied reviewed spec hash.
That establishes which plan the caller selected, not whether the caller is a
human. A local agent with the same shell/filesystem rights can invoke the same
CLI or edit the same approval files. Interactive prompts or local secrets do not
establish a separate human authority under that threat model.

Two possible deployment contracts require an explicit product decision:

1. Trust the local operator/environment. Explicit CLI approval binds exact inputs;
   default MCP cannot create preservation approval. Clearly exclude protection
   against an agent/process with equivalent local privileges. Sensitive/conflicting
   preservation stays prohibited, regardless of approval.
2. Require approval from a separately controlled authority whose signing rights
   are unavailable to the executing agent. This adds external authorization/key
   management and integration scope; do not implement it implicitly.

Neither option is selected here. Implementation/release authorization in this
conversation does not authorize preservation of a future user's source dataset.

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
