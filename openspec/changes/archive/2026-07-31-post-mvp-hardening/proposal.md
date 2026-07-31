# Change Proposal: post-mvp-hardening

## Summary

Complete the first post-MVP hardening release with lightweight packaging,
explicit DatasetSpec compatibility rules, authenticated MCP audit records, and
review-first Trino planning.

## Motivation

The base wheel installs integrations that many CSV-only users do not need.
Shared MCP workers need tamper-evident operational records. Trino planning
should use fixed allowlisted profiling tools and an explicit approval gate
without exposing raw SQL by default. Future DatasetSpec revisions also need a
predictable compatibility lifecycle.

## Scope

In scope:

- `parquet`, `mcp`, `trino`, and `all` optional dependency groups;
- fail-closed DatasetSpec version checks and deprecation policy;
- bounded HMAC-authenticated MCP audit records;
- safe Trino profile planning and explicit plan approval through MCP;
- raw-SQL MCP opt-in instead of default exposure.

Out of scope:

- public-key signatures or remote audit storage;
- automatic DatasetSpec migration;
- arbitrary SQL planning;
- production row export;
- changing DatasetSpec schema version `1.0`.

## Safety Impact

MCP audit records omit inputs and outputs, reject unsafe file targets, and
authenticate a sequence-linked event chain. Trino planning consumes only safe
profile metadata, stops before generation, and keeps raw SQL disabled by
default. Unknown DatasetSpec versions fail before data processing.

## Compatibility

CSV and JSON behavior remains available in the base installation. Parquet and
MCP/Trino users install explicit extras. Existing callers of `run_safe_select`
must opt in through `TRINO_ENABLE_SAFE_SELECT=true`. DatasetSpec `1.0` remains
the only supported schema.
