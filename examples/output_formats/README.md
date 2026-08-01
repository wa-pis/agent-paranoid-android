# Runnable Output-Format Example

This example generates the same fictional dataset as CSV, JSON, SQL, and
Parquet from one reviewed spec and seed:

```bash
examples/output_formats/run.sh /tmp/agent-paranoid-output-formats
```

Run it from an installed environment with the `parquet` extra. Every format
folder contains freshly generated synthetic rows, a validation report, and a
generation manifest. SQL output consists only of quoted `INSERT` statements;
it never converts or exports source rows.
