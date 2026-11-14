# Profile Parquet files through MCP

## Why

The generator MCP exposes `profile_csv`, but profiling a local Parquet file
currently requires a separate terminal command before the client can plan a
synthetic dataset.

## What changes

- Add `profile_parquet(input_path, output_path, table_name?)` beside
  `profile_csv`. Profile one workspace Parquet file and write a new safe JSON
  `DatasetProfile`; the client gets a relative path and summary counts.
- Reuse the current Parquet inspection and the existing saved-profile
  `plan_dataset` route. Keep the optional `parquet` extra and the existing human
  review step.

The change adds one discovery entry. It does not change any existing tool
signature or CLI artifact format. It adds no raw samples, database/provider
access, directory scanning, or transformation permission.
