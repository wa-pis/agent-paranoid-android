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

The script runs linting, strict type checks for the stable package core,
compilation, coverage tests, DatasetSpec schema freshness, and the README
quickstart smoke flow. The smoke flow verifies the generated manifest reports
`synthetic: true`, `source_rows_copied: false`, a valid validation report, the
expected seed, and expected row counts.

CI and tagged releases also build the wheel and install it in an isolated
environment. That smoke check verifies package version metadata, the PEP 561
`py.typed` marker, console entry points, and `test-data-agent doctor
--skip-smoke` before release attestations are created.

## Version And Tag

1. Bump `pyproject.toml` and `src/test_data_agent/version.py` together.
2. Move relevant `CHANGELOG.md` entries from `Unreleased` to the new version.
3. Commit the release preparation.
4. Tag the commit after `scripts/check_release.sh` passes.

Keep compatibility changes explicit: legacy `GenerationSpec` behavior should
remain a migration path, while new work should target `DatasetSpec`.

## Public Release Readiness

Before making the repository public or announcing a public release, complete
the [Public Release Checklist](public_release_checklist.md). In particular:

1. Confirm `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, issue templates, pull
   request template, and Dependabot configuration are present.
2. Confirm author and committer emails are public-safe.
3. Run a secret scan over the working tree and reachable Git history.
4. Build and smoke-test the installed wheel:

```bash
uv build --no-build-isolation
uv run --isolated --no-project --with ./dist/*.whl \
  python scripts/check_installed_package.py
uv run --isolated --no-project --with ./dist/*.whl \
  test-data-agent doctor --skip-smoke
```

5. Enable GitHub security settings after publication: secret scanning,
   Dependabot alerts, Dependabot security updates, private vulnerability
   reporting, required CI and dependency-review checks, and active branch/tag
   rulesets.
