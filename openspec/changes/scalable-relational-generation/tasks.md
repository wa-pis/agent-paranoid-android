# Tasks

## 1. Specification And Baseline

- [x] Inspect 1.7.0rc2, current guards, relationship models and deterministic/budget ADRs.
- [x] Define initial linked-table scope and explicit unsupported cases.
- [x] Validate this change with strict OpenSpec.

## 2. Deterministic Relational Core

- [ ] Add bounded DAG admission and stable parent-first planning.
- [ ] Derive synthetic FK assignments for many-to-one/one-to-one and nullable children.
- [ ] Preserve independent-engine output and reject unsupported cases before staging.

## 3. Execution, Evidence And Recovery

- [ ] Add explicit relational execution policy and reuse bounded worker scheduling.
- [ ] Enforce actual reference checks and aggregate truthful relationship metrics.
- [ ] Extend streamed validation/recovery without parent/key materialization.
- [ ] Check calibration, Python/CLI/MCP parity and exact-fingerprint review.
- [ ] Verify late-child failure, deadlines, cancellation and atomic cleanup.

## 4. Verification And Documentation

- [ ] Test chains/multiple parents/nullable/one-to-one, formats and 1/2/4-worker determinism.
- [ ] Test rejection, tampering and disabled optional validation safety.
- [ ] Measure synthetic 750k×25 linked data and record performance/memory/byte evidence.
- [ ] Update schema/contracts, guidance, roadmap and implementation map.
- [ ] Run focused and required full checks; mark only verified work complete.
- [ ] Before a separately authorized RC: independent exact-SHA review and normal release gates.
