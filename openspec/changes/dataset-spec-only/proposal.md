# Change Proposal: dataset-spec-only

## Summary

Make `DatasetSpec` the only supported generation specification in version
`0.6.0` and remove the deprecated `GenerationSpec` API.

## Motivation

The package has used `DatasetSpec` as its primary contract since `0.2.0`, but
it still carries a second model, conversion adapters, CLI fallback behavior,
artifact names, and tests for the deprecated contract. Maintaining two
generation paths makes the safety behavior harder to reason about and creates
a risk that fixes reach only one path.

## Scope

In scope:

- accept only `DatasetSpec` in the public generation and validation APIs;
- remove deprecated models, adapters, row generators, validators, and exports;
- rename the single-CSV effective spec artifact to `dataset_spec.json`;
- reject removed specification files with an actionable migration error;
- document the breaking change and migration path;
- simplify the README and point users to the documentation site.

Out of scope:

- changing the `DatasetSpec` schema version;
- removing safe adapters for older profile payloads containing `columns`;
- changing deterministic generation or validation semantics;
- splitting optional dependencies.

## Safety Impact

All generation and validation will use the same bounded, deterministic
`DatasetSpec` pipeline. Removing the parallel path reduces the chance of
inconsistent privacy, resource-limit, and validation behavior.

## Compatibility

This is a breaking package API and CLI input change for `0.6.0`. Files using
the removed contract must be rewritten as `DatasetSpec`. Safe profile payloads
remain accepted and can be converted with `infer-spec`.
