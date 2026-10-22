# Design

Reuse `pool_size`, generated identifier domains and existing relationship metrics.
Verify their adapter coverage before extending models. Censored/lower-bound
distinct counts cannot nominate a primary key or certify an exact domain.

Separate three facts: observed metadata, a proposed relationship and a reviewed
active relationship. Bind child FKs to generated parent values only after review.
Absence of declared links means untested coverage, not perfect source integrity.
Unknown source orphan/fan-out rates stay unknown; ordinary validation may still
pass the explicit spec. Any utility report must make that distinction visible.

Add explicit per-entity counts rather than repurposing --count as a scale factor.
Review EAV conditional-rule and pivot requirements as separate capabilities; the
intake does not make unimplemented domain operations mandatory in generation.

R2 implementation uses the existing catalog query to return total key arity
without expanding column authorization. Composite keys fail before aggregate
queries, including partial projections. Declared scalar INTEGER/STRING keys use
the existing synthetic identifier distribution; sensitivity and native type are
retained. Other types reject with a reviewed-spec recovery rather than generating
string tokens under an incompatible native type. No composite-key model or
source-key mapping is introduced. Existing saved profiles require reprofiling.

R3 adds `entity_counts` to direct inference and its artifact service, exposed as
repeatable `infer-spec --entity-count ENTITY=COUNT`. Exact profile entity names
are required; unknown/duplicate CLI names and nonpositive or noninteger values
reject without reflecting rejected values. Entity-specific counts override the
existing global count; untouched entities retain the previous global/profile
fallback, including the minimum one-row inference assumption.

An optional `max_total_rows` / `--max-total-rows` planning ceiling checks the sum
of resolved counts before field inference and artifact writes. It is explicitly
not a persisted runtime budget or a new environment variable. Runtime row,
output-byte and work budgets remain authoritative. Later count overrides or
load multiplication require reviewing volume again. This additive planning
contract changes no schema, default counts, seed behavior or MCP registration;
callers with no new options retain their previous behavior.
