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
