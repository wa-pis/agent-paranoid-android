# Design: cross-table-average

## Approach

Extend the existing `aggregate_mapping` operation allowlist with `avg`.
Local solving and validation ignore null child values, matching SQL `avg`
semantics. A group with no numeric values resolves to zero, matching the
existing outer `COALESCE` behavior used by Trino profiling.

Inference recognizes parent fields named
`<child_entity>_<child_field>_average` or
`<child_entity>_<child_field>_avg`.

## Safety Decisions

- Keep aggregate names allowlisted.
- Cast only an allowlisted, quoted child column in generated Trino SQL.
- Return counts, confidence, and residuals rather than child values.
- Treat non-numeric local child values as validation failures.

## Alternatives

Arbitrary SQL aggregate expressions were rejected because they would expand
the Trino query surface. Median and percentile mappings were deferred because
their cross-engine semantics need a separate contract.
