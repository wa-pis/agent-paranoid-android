# Change Proposal: cross-table-average

## Summary

Add average reconciliation to cross-table aggregate mappings.

## Motivation

Existing mappings preserve child sums and counts, but parent summary tables
also commonly store average values.

## Scope

In scope:

- `avg` in the aggregate mapping contract;
- deterministic solver and validator support;
- safe naming-based inference for `_average` and `_avg` parent fields;
- read-only Trino aggregate profiling.

Out of scope:

- arbitrary aggregate expressions;
- multi-hop relationships;
- controlled negative scenarios.

## Safety Impact

Trino profiling remains a fixed aggregate-only query. No child rows or raw
values are returned.

## Compatibility

Existing sum and count mappings are unchanged.
