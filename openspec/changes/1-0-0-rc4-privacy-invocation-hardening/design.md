# Design: 1-0-0-rc4-privacy-invocation-hardening

## Approach

Implement the hardening in four bounded stages:

1. Make the default Trino MCP registration aggregate/metadata-only and remove
   `sample_rows_masked` from the public compatibility surface, rather than
   preserving a misleading masked-row capability. Keep `run_safe_select` as a
   separately enabled, explicitly non-source-free capability. Add a
   source-literal regression harness that uses distinct values in all columns,
   including non-PII-looking values and varied SQL types.
2. Create a typed `QueryWorkBudget` owned by the Trino application boundary.
   Enforce a raw transport payload limit before MCP argument parsing and a
   canonical serialized-argument limit after schema validation. Create one
   fresh budget per invocation, pass the same non-resettable object through
   nested profiling and query helpers, and isolate it from concurrent
   invocations. Decrement shared request, statement, column, AST, and response
   allowances; check each limit before the operation that could consume it and
   fail closed with a bounded typed error. Consume response bytes incrementally
   while constructing results, before a complete oversized response is held in
   memory.
3. Update prerelease installation examples, MCP safety language, contract
   fixtures, and release documentation. The clean-environment check must use
   the exact command shown to users and assert the installed RC version.
4. Publish RC4 only after the direct API, integration, artifact, documentation,
   and security gates pass on the exact verified commit. Stable promotion then
   reuses that accepted commit and does not reopen feature scope.

## Data And Contracts

- `src/test_data_agent/mcp_trino_server.py`: default tool registration,
  removal of the row-sampling wrapper, and independent `run_safe_select`
  opt-in.
- `src/test_data_agent/trino_masking.py` and `trino_query_builders.py`: remove
  the row-sampling path from the RC4 public surface; no heuristic masking path
  may be presented as a guarantee that arbitrary source literals are absent.
- `src/test_data_agent/trino_client.py`, `trino_profiling.py`, and
  `trino_config.py`, plus MCP transport composition: typed shared invocation
  budget, raw/canonical input limits, lifecycle, and enforcement points.
- `tests/fixtures/contracts/mcp-trino-tools.json` and Trino tests: updated
  default tool contract, full registered-toolset checks, and adversarial
  no-literal assertions over serialized responses, errors, and audit records.
- `openspec/specs/safe-mcp-workflow/spec.md` and MCP documentation: explicit
  aggregate-only/default versus opt-in/row-returning semantics.
- `README.md`, `docs/getting-started/installation.md`, and release checks:
  exact prerelease installation and clean public-artifact quickstart.
- `pyproject.toml` and installation smoke profiles: preserve the base runtime
  without `trino`, `sqlglot`, or the MCP SDK; keep Trino checks behind the
  separate `trino` extra.
- Release metadata, changelog, attestations, container tags, and public
  acceptance evidence: all identify the exact `1.0.0rc4` commit/artifact.

The budget should be represented as a typed model rather than an unstructured
dictionary. It must cover at least raw transport payload bytes, canonical
argument bytes, SQL/formula characters, AST nodes and depth, projected columns,
statements, and response bytes. Counters are monotonic and cannot be reset by
helpers. A failed or rejected operation does not restore consumed work, and no
later statement runs after exhaustion.

## Failure Modes

- An unsafe or over-budget request fails before opening a Trino connection or
  cursor whenever the required information is available at validation time.
- A budget exhausted during nested profiling stops the invocation and returns a
  bounded typed error; it must not continue with later columns or statements.
- A source-literal regression fails if any distinct test fixture value appears
  in the default MCP response, error, or audit payload after JSON
  serialization, across strings, numbers, decimals, booleans, dates,
  timestamps, UUID-like values, Unicode, binary-like values, nested JSON, and
  null mixtures.
- `sample_rows_masked` is unavailable through the RC4 public MCP and Python
  compatibility surfaces. `run_safe_select` is unavailable unless its
  independent opt-in is enabled and remains outside the source-free guarantee.
- A raw transport payload over its limit fails before argument parsing; a
  canonical argument over its limit fails before database access. A response
  over its byte budget stops accumulation before the complete response is
  materialized.
- A public RC4 install or README smoke failure blocks stable promotion; no local
  checkout-only success is sufficient.
- Atomic publication continues to protect visibility and process-interruption
  recovery. Crash/power-loss durability remains an explicit documented
  decision, not an accidental guarantee.

## Durability Disposition

Artifact publication guarantees same-filesystem atomic visibility where a
single file or new directory is replaced, plus in-process cleanup, rollback,
and agent recovery for failures the process can handle. Multi-file updates are
not one filesystem transaction. Artifact writers do not fsync file contents or
parent-directory metadata, so crash, storage, and power-loss durability is not
promised.

Artifact fsync is deferred until after 1.0 and is not release-blocking for RC4
or stable 1.0. The repository maintainer owns reconsideration before any public
crash-durability promise, when deployment requirements demand it, after an
artifact-loss incident, or when platform-specific implementation and
crash-consistency tests are ready.

## Remaining Finding Register

No unresolved P0 or release-blocking P1 implementation finding remains in this
change. The residual Medium and P2/P3 risks are dispositioned below; the exact
RC4 security pipeline may supersede a carried-forward scanner finding only
with evidence from the candidate commit.

| ID | Priority | Finding | Owner | Disposition | Revisit date and triggers |
| --- | --- | --- | --- | --- | --- |
| RC4-F1 | Medium | Scorecard SAST coverage score of 8 is carried forward from the RC2 review until an exact-RC4 Scorecard result supersedes it. | Repository maintainer (`@wa-pis`). | Accepted as a non-release-blocking CI maturity risk; code-affecting changes retain required CodeQL. | 2026-11-01; review immediately if code can merge without CodeQL, path classification broadens, the score falls below 8, or another maintainer joins. |
| RC4-F2 | P2/P3 | Artifact writes do not promise crash or power-loss durability without file and directory `fsync`. | Repository maintainer (`@wa-pis`). | Deferred until after 1.0; not release-blocking while the public contract makes no crash-durability promise. | 2026-11-01 or the first post-1.0 hardening cycle; review immediately for a public durability promise, deployment requirement, artifact-loss incident, or platform crash-test plan. |
| RC4-F3 | P2 | Opt-in `run_safe_select` rows may contain allowed source values or values missed by heuristic masking. | Repository maintainer (`@wa-pis`) for implementation; deploying operator for enablement. | Accepted as an explicit, disabled-by-default contract risk outside the source-literal-free guarantee. | 2026-11-01; review immediately before default enablement, a source-free claim, a new row-returning capability, returned values in errors or audit records, or a query/privacy incident. |

The public-wheel clean-environment check and exact-commit package, container,
documentation, attestation, signature, and integration checks were pending
release evidence, not findings before publication.
They remain release-blocking tasks for any replacement candidate and completed
successfully for `v1.0.0rc4`. The
immutable commit, workflow runs, package hashes, and container
digests are recorded in the
[RC4 published-release evidence](../../../docs/release-evidence-1.0.0rc4.md).

## Stable Promotion Contract

The accepted RC4 baseline is the exact annotated `v1.0.0rc4` tag commit after
all public-artifact acceptance checks pass. Stable promotion compares its
entire tree to that immutable commit. The only allowed changes are package and
lockfile root-version metadata, release-status classifiers, changelog
classification, already-accepted version references, release evidence,
roadmap status, and OpenSpec completion or archive metadata.

Every changed hunk must be reviewed as release metadata. Production code,
tests, schemas, fixtures, dependency resolution, build configuration,
workflows, and container definitions remain byte-for-byte at the accepted RC4
state. If any of them must change, stable promotion stops and the fix must pass
through a newly numbered release candidate and public acceptance. All final
release gates run again on the exact stable release commit before its verified
`main` merge commit can be tagged.

## Alternatives

- Retain heuristic `sample_rows_masked` behind a new opt-in in RC4: rejected;
  its presence would create an ambiguous source-free contract and its unknown
  literals can pass through unchanged. A future row-returning capability needs
  a separate reviewed proposal.
- Add more per-query limits only: rejected because fan-out profiling can still
  exceed a safe invocation budget.
- Publish stable directly from the merged RC3 refactor: rejected until the P0
  privacy and P1 release-budget findings are closed.
- Promise fsync durability in this RC: deferred unless product requirements
  explicitly include crash/power-loss durability; otherwise document the
  current guarantee precisely.
