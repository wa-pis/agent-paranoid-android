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
