# DatasetSpec Compatibility

`DatasetSpec.schema_version` versions the serialized YAML and JSON contract
between planners, reviewers, generators, and validators. It is separate from
the Python package version.

## Current Support

| Schema version | Status | First package release |
|---|---|---|
| `1.0` | Supported | `0.3.0` |

Files without `schema_version` are interpreted as `1.0` for compatibility with
early project artifacts. New files always include the field.

Readers fail closed on every version that is not explicitly supported. They do
not guess how to interpret a newer contract or silently downgrade it.

## Version Rules

Schema versions use `MAJOR.MINOR`.

- Increment `MINOR` for backward-compatible additions, such as an optional
  field with a safe default.
- Increment `MAJOR` when an existing field changes meaning, becomes required,
  is removed, or accepts a narrower value set.
- Package patch releases do not change DatasetSpec semantics.
- Every schema change includes an OpenSpec update, regenerated JSON Schema,
  migration tests, and release notes.

Support for a new schema version is explicit in
`SUPPORTED_DATASET_SPEC_SCHEMA_VERSIONS`. A reader may support multiple schema
versions only when each version has a tested parser or migration path.

## Deprecation And Removal

A schema version is deprecated before removal:

1. Mark it in `DEPRECATED_DATASET_SPEC_SCHEMA_VERSIONS`.
2. Publish a migration guide and changelog notice.
3. Keep reading it for at least one feature release and 90 days.
4. Remove it only in a release identified as breaking.

An urgent security issue may shorten this period. The release notes must name
the issue, affected versions, and safe migration path.

Generation manifests retain the exact DatasetSpec fingerprint. Migration must
produce a new reviewed DatasetSpec and must never rewrite an existing generated
bundle in place.
