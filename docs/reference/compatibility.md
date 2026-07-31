# Compatibility Surfaces

This inventory covers aliases and wrappers retained while the package
converges on its `1.0` public API. New code should use the canonical surface,
but retained entries remain tested for their stated window.

## Command Aliases

| Retained command | Canonical command | Status | Support window |
| --- | --- | --- | --- |
| `profile-csv-folder` | `profile-example` | Supported alias | Through all `1.x` releases |
| `generate-from-csv-folder` | `generate-from-example` | Supported alias | Through all `1.x` releases |

The aliases accept the canonical command's options and reach the same
application dispatch. Help output labels the canonical command. They are not
currently deprecated.

## Python Compatibility Wrappers

| Retained import | Canonical import | Status | Support window |
| --- | --- | --- | --- |
| `test_data_agent.business_rules` | `test_data_agent.rules.models` | Supported wrapper | Through all `1.x` releases |
| `test_data_agent.business_validator` | `test_data_agent.rules.validation` | Supported wrapper | Through all `1.x` releases |
| `test_data_agent.rules_engine` | `test_data_agent.rules.engine` | Supported wrapper | Through all `1.x` releases |
| `test_data_agent.scenario` | `test_data_agent.rules.scenarios` | Supported wrapper | Through all `1.x` releases |

These modules re-export the canonical objects; they do not maintain parallel
implementations. Their `__all__` lists define the retained names. New code
should import from `test_data_agent.rules`.

## Transitional Model Access

`AgentSummary` subclasses currently support `summary["field"]` and
`summary.get("field")` in addition to typed attributes. This mapping-style
access is transitional and retained through all `1.x` releases. New code
should use `summary.field` so type checkers can validate the access.

Mapping-style access is not deprecated yet. Any future deprecation must first
ship a warning and migration note, then remain available for at least one
feature release and 90 days. Removal cannot occur before `2.0`.

## Already Removed

The old `GenerationSpec` API was deprecated in `0.2.0` and removed in `0.6.0`.
It is not a retained compatibility surface. Loaders reject its shape with a
link to [Migrating To 0.6](../operations/migrating-to-0.6.md).

Safe legacy profile JSON with top-level `columns` remains a supported input
adapter. It is converted to safe profile metadata, not treated as a generation
specification.

## Deprecation Policy

For a currently supported alias or wrapper:

1. publish the replacement and migration example;
2. mark the surface deprecated in this inventory and the changelog;
3. emit a non-secret, non-row deprecation warning where practical;
4. retain it for at least one feature release and 90 days;
5. remove it only in a release whose compatibility policy permits the break.

Urgent security fixes may shorten the window. The security advisory and
release notes must identify the affected surface and safe replacement.

Contract tests cover the CLI aliases, wrapper identity and behavior, and
transitional summary access. See [Public Stability](stability.md) for the
broader compatibility rules.
