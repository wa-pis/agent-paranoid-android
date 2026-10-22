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

R4 exposes existing deterministic discovery through a saved-profile-only CLI.
A typed JSON report binds candidates to the existing canonical profile
fingerprint and explicitly denies generation authority. Candidate evidence and
field references exclude distribution literals. Same names/types and aggregate
counts do not establish overlap or domain identity; competing parents remain
unresolved. Only references already in the supplied profile are considered;
there is no database/provider lookup or additional authorization surface.

The existing LocalProfileBudget is shared across metadata iteration, foreign-key
and temporal candidate comparisons. Candidate count is capped at 1,000; input
profile and output report use the existing profile-payload byte ceiling. A
budget/cap failure publishes no partial report. Existing direct mining calls
retain their candidate identity/order but gain bounded execution and explicit
untested-domain assumptions. Review remains separate from DatasetSpec authoring
and cannot approve or activate generation.

The report has an explicit `relationship_discovery` artifact type. DatasetSpec
validation rejects this type across direct and file/CLI consumers instead of
silently interpreting it as an empty spec. The shared local deadline is checked
again by the atomic writer immediately before report publication.

R5 extends the existing validation report with optional typed `utility` evidence;
new validation calls always populate it, while legacy reports remain readable.
The canonical spec hash binds evidence to its declarations; its shared pure
helper moves to core with I/O wrappers and digest semantics retained.
Active declarations exclude rejected relationships/constraints. Executed,
not-declared and not-run states distinguish disabled and fail-fast skips.
Existing generated relationship key-domain/resolution metrics are retained;
native temporal counts are collected inside their existing budgeted row loop.
No source comparison is made: unmodeled relationship counts, orphan rate and
fan-out stay null, and source temporal fidelity remains unmeasured. Empty
relations provide zero observations, not a successful source-fidelity claim.
Business-rule temporal checks retain their separate business-validation evidence.
