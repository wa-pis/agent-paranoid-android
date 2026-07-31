# Change: previous-release-fixtures

## Why

Current golden fixtures detect present-day drift but do not prove that a new
package still reads reviewed artifacts from an already published feature
release.

## What Changes

- Preserve row-free spec and manifest fixtures from annotated tag `v0.11.0`.
- Record exact source provenance.
- Generate and validate a compatible bundle with the current package.

## Safety

The baseline contains synthetic metadata only and no generated or source rows.
