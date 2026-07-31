# Runnable CSV Quickstart

This example uses fictional input and runs the explicit safe workflow:

```text
profile CSV -> reviewable spec -> deterministic generation -> validation
```

From an environment where `test-data-agent` is installed:

```bash
examples/csv_quickstart/run.sh /tmp/agent-paranoid-csv-example
```

The output contains the safe profile, inferred spec, generated CSV bundle,
generation manifest, original validation report, and independent revalidation
report. The source rows are profiling input only and are never shuffled or
copied into generated output.

Use a new output path for each run. Seed `12345` makes the generated dataset
reproducible in the same supported environment.
