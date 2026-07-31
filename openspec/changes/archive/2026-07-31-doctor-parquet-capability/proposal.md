# Change: doctor-parquet-capability

## Why

Importing PyArrow does not prove that an installed wheel can generate and read
the Parquet artifacts users rely on.

## What Changes

- Run a temporary Parquet generation and read-back when the extra is required.
- Validate entity row counts, output format, and manifest safety flags.
- Redact underlying failure details and provide exact reinstall guidance.
- Exercise the smoke from the isolated Parquet wheel profile in CI.

## Impact

`doctor --require-extra parquet` performs additional local temporary work unless
`--skip-smoke` is supplied. It does not contact external services.
