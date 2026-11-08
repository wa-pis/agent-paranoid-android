# Change Proposal: Scalable Relational Generation

## Status

Initial linked-table scope implemented and verified, unreleased. The owner
authorized the OpenSpec and implementation on 2026-11-08. The performance
target remains unmet at 1.953× four-worker median; see evidence.md. Baseline: published 1.7.0rc2, exact package
source b996da8e4db1435406ac39b5294d234c4a9f9c6c; development starts from main
b1614e333e875a3373105011d937f828de73a2ff. No new release is authorized here.

## Why

The scalable engine currently rejects every relationship. Users with large
parent/child datasets must return to the in-memory engine and its conservative
limits. Parallel generation must retain actual FK integrity and distinct rows,
not merely make each table look individually plausible.

## What Changes

Add opt-in `scalable-relational-v1` for acyclic single-column many-to-one and
one-to-one relationships referencing generated synthetic primary keys. Include
chains, multiple parent tables, unequal counts and nullable child references.
Generate tables in stable dependency order, batching each table across 1–4
processes. Derive parent keys from seed/domain/ordinal without retaining parent
rows or a key pool. Preserve unique child primary keys and reject unsupported
combinations before staging output. Validate actual references and report
count-only relationship evidence during generation and streamed recovery.
Expose the same reviewed policy through existing Python, CLI and MCP workflows;
engine changes invalidate prior approval. Retain scalable-v1 and legacy seeded
outputs. Keep budgets, deadlines, private staging and atomic publication.

## Initial Scope And Explicit Deferrals

Support valid/edge modes, CSV/JSON/Parquet and Linux/macOS as in scalable-v1.
Reject cycles/self-links, non-PK parents, PK-as-FK/shared identity, incompatible
key types, insufficient one-to-one parent domains, global/native/business rules,
relational scenarios and negative/mixed/load modes. Composite relationships are
not in the existing single-field model. Those need separate executable designs;
no silent fallback, dropped relationships or blanket relaxation of guards.
Source preservation, source identifier reuse, database access and Windows
resource-accounting support are outside this change.

## Acceptance

Prove FK resolution and one-to-one uniqueness, mandatory schema/privacy checks,
worker/batch determinism, bounded graph admission and streamed validation,
cleanup/recovery and approval invalidation using fictional fixtures only.
Benchmark linked datasets including 750k total rows and 25 columns/table; publish
actual 1/2/4-worker time, bytes and conservative memory bounds. Target >=2x
four-worker speedup over serial relational streaming on a suitable multicore
host; report an unmet target explicitly rather than claiming performance.
