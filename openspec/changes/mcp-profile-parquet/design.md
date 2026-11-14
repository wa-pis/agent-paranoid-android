# Design: profile_parquet

Resolve paths using the generator workspace policy. Require a single regular
`.parquet` source and a different, new `.json` destination. Read using the
existing no-follow regular-file opener after resolution. Use the current
Parquet adapter and safe profile validation; keep the compressed input,
row, column, cell, decoded-byte and local/request time limits. Publish
atomically without replacing an existing file. Deadline checks are cooperative
and do not interrupt native decoders or filesystem calls in progress.

The tool accepts `input_path` and `output_path` strings and an optional
`table_name`, defaulting to the source stem. It returns `operation`,
`profile_path`, `source_type`, `entity_count` and per-entity name, row, field and
sensitive-field counts. The JSON artifact retains the adapter's existing
schema and uncertainty: exact or lower-bound distinct ratios are labelled,
and unavailable distinct/null measurements stay unknown. Neither surface
returns source rows, cell values, private distinctness digests or embedded
file metadata. Reject schema/table names that themselves match recognizable
sensitive values. Source values are inspected only inside the bounded profiler.

Missing PyArrow yields a fixed hint to install the `parquet` extra; other
failures follow existing MCP redaction. A failed call publishes no trusted
profile. Clients can submit a successful artifact via `plan_dataset` with
`source_type: "profile"`. Insufficient evidence still needs a reviewed
specification, and profiling does not approve generation.
