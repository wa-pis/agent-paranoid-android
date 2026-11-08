# Tasks

## 1. Specification And Baseline

- [x] Inspect 1.7.0rc2, current guards, relationship models and deterministic/budget ADRs.
- [x] Define initial linked-table scope and explicit unsupported cases.
- [x] Validate this change with strict OpenSpec.

## 2. Deterministic Relational Core

- [x] Add bounded DAG admission and stable parent-first planning.
- [x] Derive synthetic FK assignments for many-to-one/one-to-one and nullable children.
- [x] Preserve independent-engine output and reject unsupported cases before staging.

## 3. Execution, Evidence And Recovery

- [x] Add explicit relational execution policy and reuse bounded worker scheduling.
- [x] Enforce actual reference checks and aggregate truthful relationship metrics.
- [x] Extend streamed validation/recovery without parent/key materialization.
- [x] Check calibration, Python/CLI/MCP parity and exact-fingerprint review.
- [x] Verify late-child failure, deadlines, cancellation and atomic cleanup.

## 4. Verification And Documentation

- [x] Test chains/multiple parents/nullable/one-to-one, formats and 1/2/4-worker determinism.
- [x] Test rejection, tampering and disabled optional validation safety.
- [x] Measure synthetic 750k×25 linked data and record performance/memory/byte evidence (1.953× median; ≥2× target not met).
- [x] Update schema/contracts, guidance, roadmap and implementation map.
- [x] Run focused and required full checks; mark only verified work complete.
- [ ] Before a separately authorized RC: independent exact-SHA review and normal release gates.
