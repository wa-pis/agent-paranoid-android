# Cross-interface acceptance campaign

## Status and trigger

Planned at the owner's request on 2026-10-16. Execute after the current feedback,
source/output parity and MCP documentation work is complete, before declaring
that work accepted or preparing its next release. This change records the plan;
it does not claim that the campaign has run. Earlier successful checks remain
historical evidence, not acceptance of a later SHA.

## Why

The shared source/output regression matrix does not by itself prove equivalent
installed CLI, Python and real MCP behavior, complete option coverage, working
container workloads or actual database acquisition. The owner requested one
final campaign covering these layers and their interactions.

## What changes

- Maintain a finite coverage ledger derived from the public schemas, CLI parser,
  Python exports, MCP discovery, supported environments and source/output matrix.
- Reuse the 200 source/output/mode cases and exercise their supported compositions
  through installed Python, CLI and real stdio MCP, not direct MCP helper calls.
- Cover every option family, boundary values, compatible option pairs and named
  high-risk interactions; report uncovered required cases explicitly.
- Verify permission refusal, review/recovery, budgets, publication rollback,
  redaction and artifact revalidation, including controlled-invalid results.
- Run isolated fictional database and separately gated transformation campaigns,
  optional dependencies and real hardened-container workloads.
- Bind a value-free acceptance report to one exact commit and built artifacts.

The executable sequence and completion criteria are in
`docs/acceptance-matrix.md`. Execution is in progress. The campaign found and
repairs negative/mixed collateral accounting for overlapping local and aggregate
rules, tiny CSV DECIMAL serialization and signed maximum-scale DECIMAL parsing.
Executable installed-interface runners, a finite measured option covering array
and hardened container workloads accompany the tests. Retained identifier-prefix
metadata is now distinguished from an effective generation control. Completion
remains conditional on the final evidence and manual gates.

## Safety and compatibility

No new commands, flags, permissions, credentials, live external data access,
transformation activation, release version, publication or protection bypass is
authorized by this plan. Use fictional local fixtures and disposable databases;
providers use fictional transports. Preserve existing local human approval
boundaries. Distinguish an interface's native flags from settings carried by a
reviewed DatasetSpec; do not mark a missing required generation behavior N/A
merely because a convenience wrapper lacks a flag.
