# ADR-0016: Keep public contracts versioned and integrations optional

- Status: Accepted — retrospective baseline.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Internal refactors and dependency updates can change external behavior without changing command names. Users should not install every integration to use deterministic CSV/JSON workflows.

## Decision

Document supported top-level Python exports, CLI/MCP schemas, artifact layouts and DatasetSpec versions. Protect them with reviewed golden catalogs and immutable prior-release fixtures; do not regenerate fixtures merely to hide a regression.

Keep base deterministic CSV/JSON installation separate from optional Parquet, MCP, database and provider extras. Test installed wheels and minimum/latest dependency profiles on supported CPython versions. A declared version range alone is not support evidence; provider adapter maturity is separate from the stability of its neutral contract.

## Alternatives and consequences

Treating every internal module as public prevents refactoring. Bundling all SDKs enlarges installation/security cost. A lockfile is tested-environment evidence, not a future-version guarantee. Speculative dependency caps are not justified without a reproduced incompatibility.

## Evidence

Sources: [stability](../reference/stability.md), [runtime support](../reference/support-policy.md), [dependency compatibility](../reference/dependency-compatibility.md).
Executable anchors: [contract fixtures](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_contract_fixtures.py), [previous release](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_previous_release_compatibility.py), [installed package](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_installed_package.py).

## Revisit when

Removing an extra/runtime/export or changing defaults requires the documented compatibility/migration process.

