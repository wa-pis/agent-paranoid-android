# Change Proposal: relational-profile-utility

## Summary
Make relational planning and its limits reviewable: preserve supported repeated
synthetic key pools, propose logical relationships without executing hypotheses,
and distinguish validation of declared structure from measured source fidelity.

## Motivation
Feedback A/B/F/G and #8/#13/#14 mixes older key-generation bugs with absent domain
relationships. Main fixes key-domain collisions and declared FK assignment, but
an empty relationship list still cannot establish usefulness for joins.

## Scope
P1: audit pools across CSV/PostgreSQL/query/Parquet; arbitrary and composite PK
metadata; explicit per-entity sizing; bounded metadata-only relationship candidates;
utility/coverage evidence including unknowns; reviewable orphan behavior.

Out of scope: source key preservation, implicit FK activation, copying orphan rows,
automatic pivot/unpivot, or silently changing existing --count semantics.

## Safety Impact
Use only counts, authorized schema metadata and reviewed declarations. Do not
probe unauthorized parent tables or fetch raw keys. Candidates are hypotheses;
only approved relationships bind independently generated keys. No broader SQL
or preservation authority is granted.

## Compatibility
New sizing/utility interfaces must be additive and hash-bound. Composite keys
must be represented correctly or explicitly rejected, never reduced silently.
Generation-changing work requires migration evidence and an RC.
