# Runnable Relational CSV Example

This fictional customer/order dataset demonstrates a reviewable multi-table
workflow with inferred relationships and deterministic business rules.

```bash
examples/relational_csv/run.sh /tmp/agent-paranoid-relational-example
```

The launcher profiles the input folder, writes a reviewable spec, generates
both tables with seed `24680`, applies `rules.yaml`, and independently validates
the generated bundle. For a real domain, stop after `infer-spec`, review every
relationship and rule, then run the remaining commands manually.

The CI regression verifies that generated order foreign keys reference only
generated customers, formula and temporal rules pass, and no source rows are
reported as copied.
