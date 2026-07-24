# Design: dataset-spec-only

## Approach

The CLI will route `generate` and `validate` directly to the dataset-oriented
commands. The `DatasetSpec` loader will identify the removed top-level
`table`/`tables` shape before Pydantic validation and return a concise error
that links to the migration guide.

The old package modules and compatibility package will be deleted. The package
root will expose only the domain-oriented API.

Single-CSV workflows already build a `DatasetSpec`; their effective spec file
will be renamed from `generation_spec.json` to `dataset_spec.json`.

## Retained Input Compatibility

Profile payloads with top-level `columns` are metadata inputs, not generation
specifications. Their adapter remains supported but will use profiling types
instead of importing removed specification models.

## Failure Modes

- A removed specification shape fails before generation or validation starts.
- A malformed `DatasetSpec` reports its first validation error through the
  existing CLI error boundary.
- Validation continues to require a dataset output folder.
- Existing output folders are never partially rewritten during a failed
  migration attempt.

## Alternatives

Keeping conversion adapters for another release was rejected because the
compatibility path has emitted deprecation warnings since `0.2.0`, and `0.6.0`
is the planned breaking cleanup release.

Silently converting removed files was rejected because conversion can lose
intent and would keep the second contract operational.
