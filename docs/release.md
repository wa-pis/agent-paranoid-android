# Release Process

Use this process before merging release candidates or creating tags.

## Preflight

1. Review `openspec/project.md` and the affected capability specs.
2. Confirm the change belongs in the MVP or has an OpenSpec proposal under
   `openspec/changes/`.
3. Update README examples, `CHANGELOG.md`, and user-facing docs for visible
   behavior changes.
4. Regenerate `schemas/dataset_spec.schema.json` when `DatasetSpec` changes:

```bash
python3 scripts/export_dataset_schema.py
```

## Checks

Run the executable release gate:

```bash
scripts/check_release.sh
```

The script runs linting, compilation, coverage tests, DatasetSpec schema
freshness, and the README quickstart smoke flow. The smoke flow verifies the
generated manifest reports `synthetic: true`, `source_rows_copied: false`, a
valid validation report, the expected seed, and expected row counts.

## Version And Tag

1. Bump `pyproject.toml` and `src/test_data_agent/version.py` together.
2. Move relevant `CHANGELOG.md` entries from `Unreleased` to the new version.
3. Commit the release preparation.
4. Tag the commit after `scripts/check_release.sh` passes.

Keep compatibility changes explicit: legacy `GenerationSpec` behavior should
remain a migration path, while new work should target `DatasetSpec`.
