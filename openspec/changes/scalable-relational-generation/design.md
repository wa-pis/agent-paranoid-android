# Design: Scalable Relational Generation

## Compatibility And Ownership

Follow ADR-0005 deterministic provenance, ADR-0007 executable rules and
ADR-0015 explicit resource budgets. This extends those decisions without
changing them. `scalable-v1` keeps its independent-table admission and output.
A new execution-policy engine names the relational algorithm and participates
in spec fingerprints, approval, manifests, calibration and recovery.

Pure planning/key assignment belongs in generation, publication in io/scalable,
and streamed readback in io/scalable_validation. Reuse existing synthetic keys,
typed relationship metadata, mandatory batch checks and report models. Do not
add a graph dependency or an unbounded set of parent/child keys.

## Graph Admission

Bound specification graph size before traversal. Ignore rejected hypotheses;
all other relationships retain current active semantics. Require each target
to be the parent's non-null synthetic integer/string primary key and each child
FK to differ from its own PK. Reject unsupported rules and modes, cycles,
self-links, duplicate/conflicting targets, insufficient one-to-one domains and
type mismatches before any staging allocation. Stable Kahn traversal uses
original entity order to break ties; original entity/field order still defines
random streams and disjoint identifier domains. Complete parent tables before
starting children; parallelize bounded row batches within a table.

## Synthetic Reference Assignment

Parent keys use existing synthetic_identifier(seed, field-domain, ordinal).
Many-to-one uses a dedicated row/relationship-local deterministic stream and a
uniform parent ordinal. One-to-one uses the child's global row ordinal, which
is unique and bounded by the admitted parent count. Retain generated nullable
FK masks and never fetch source or generated parent rows. Relationship order
is part of the ordered spec/engine identity. No source frequency/fanout fidelity
is inferred from this assignment.

## Mandatory Validation And Evidence

After assignment, check each actual non-null FK against the expected synthetic
parent ordinal/key. Validate nullable references and one-to-one assignment even
when optional reporting is disabled. Batch schema/privacy validation uses a
relationship-free chunk only after these checks, avoiding false missing-parent
errors from partial batches. Accumulate checked/resolved/null counts for the
existing RelationshipMetrics model. Zero active relationships remains
not_declared, while actual executed relationships are reported executed with
counts; do not reuse the independent-table report's zero checks.

Streamed recovery verifies every parent's actual key domain/order/count and
every child's deterministic assignment, hashes and normal mandatory safety
checks. It never loads entire parent tables. Failure in a late child prevents
publication of all tables. The same invocation deadline covers graph planning,
parent/child generation, checks, writing and publication; workers are reaped on
failure. Graph work and FK checks must charge the existing work allowance.

## Calibration And Acceptance

Calibration preserves admitted parent/child cardinality under bounded sample
counts and retains the 200k-cell/16MiB/30-second ceilings. Metadata estimates
must not certify unsupported relational execution. Existing CLI/MCP surfaces
accept the new typed policy; summaries expose no rows or new approval issuer.
Use fictional two-/three-level DAGs, multiple FKs, nulls, one-to-one, shuffled
entity order and rejected hypotheses. Compare CSV/JSON bytes and logical Parquet
rows across workers/batches. Tampered child links must fail readback even with
updated file hashes. Measure linked 750k×25 total scale and smaller regressions
without claiming the independent-table benchmark as relational evidence.
