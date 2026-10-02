# ADR-0029: Use one explicit replacement contract for every field

- Status: Accepted — explicit owner decision 2026-10-02; public execution gated.
- Recorded: 2026-10-02.

## Context

ActivationSafety-R2 finding R2-1 described typed mappings that permute sensitive
source values. The owner explicitly accepted this behavior: replacement has one
contract for all fields and apparent sensitivity must be noted at the field,
not used to prohibit a mapping merely because its result occurs in the source.

## Decision

Explicit `substitute` and `replace_text` mappings may produce values equal to
another source value, including values in sensitive fields and mapped
permutations. Apply mappings once to bound source bytes with unchanged typed
matching, duplicate-key, scope, identity-pair and unmatched-action rules.
Do not infer origin from membership or equality: an applied mapping is replacement.
Keep effective sensitivity and a bounded value-free note visible in review.

This narrowly supersedes the source-membership prohibition for explicit mappings,
not ADR-0021's direct `preserve`/preserve-fallback authority. Those still require
non-sensitive decisions, comments and local TTY receipts; DECIMAL preservation
is unchanged. No implicit copy fallback, source-free generation reuse, raw values
in profiles/review/logs/errors/summaries/providers/MCP, or real data access granted.

Public activation requires the updated baseline/OpenSpec contract, executable
tests and independent review of the finished immutable activation SHA. Old review
343305e does not approve this changed policy. Remaining R2-2/3/4 are unaffected.

## Evidence

Owner conversation 2026-10-02: “да разрешаю контракт замен - единый для всех”,
followed by explicit instructions to implement. See the owner amendment in
`openspec/changes/selective-source-transformation/policy-contract.md` and the
historical report `activation-safety-r2.md` there. No human GitHub approval claimed.

See the [policy contract](https://github.com/wa-pis/agent-paranoid-android/blob/915536ae2240ad2475149a7e02418f741ca7d716/openspec/changes/selective-source-transformation/policy-contract.md)
and [historical independent AI review](https://github.com/wa-pis/agent-paranoid-android/blob/915536ae2240ad2475149a7e02418f741ca7d716/openspec/changes/selective-source-transformation/activation-safety-r2.md).

## Alternatives and consequences

Keeping a source-membership ban would contradict the explicit owner decision.
Instead, deterministic mapped-cell evidence confines the exception to actual
replacement output. Direct preservation and transport disclosure retain their
separate restrictions. Sensitive mapped artifacts require local handling and
are not synthetic datasets; sensitivity notes do not declassify their contents.

## Revisit when

An owner-authorized successor changes replacement semantics or output disclosure.
Any such amendment requires executable safety evidence and independent review
of its complete exact SHA before public activation.
