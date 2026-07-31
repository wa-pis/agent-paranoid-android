# Runnable Python API Example

This example consumes only the documented package-root API. Its input is a
fictional metadata profile, not source rows.

```bash
python examples/python_api/run.py /tmp/agent-paranoid-python-api
```

The script infers a reviewable `DatasetSpec`, generates 16 JSON records with
seed `314159`, writes the normal generation bundle, and independently validates
the exported rows. For a real domain, inspect and approve the saved
`reviewed_spec.json` before calling `generate_dataset_bundle`.
