# Transformation follow-through — 2026-11-09

This reconciles the two remaining composite tasks against published 1.7.0rc3.
It changes no runtime, accepted ADR, source access, preservation permission or
public registration. Both parent tasks remain open. Earlier approvals, private
scale results and releases retain their actual source/artifact identities.

## Source and fresh executable evidence

- Audited main: `09be40b0d145699c804d6a8de6fdb9c5f2767bc1` (post-release evidence).
- Published package source: `09b6fb207b22364ff41f70d7b51abe30d1a458fa`.
- Exact public Ubuntu wheel SHA-256:
  `5345e27a5a8311d72cedda193747c861f2d646ef0de374bd9bd74e1405c5195d`.
- Fresh isolated installed-only replay: Python 3.15.2, macOS arm64, MCP 2.2.0,
  PyArrow 26.0.1; frozen hash-checked all-extra dependency export. Import location
  was verified under the isolated environment, outside the checkout. The clean
  child environment omitted provider/database credentials and PYTHONPATH.
- Unchanged `scripts/accept_transformation_routes.py --public`, SHA-256
  `b8cf5366a5ec9716066dd83c0fcab1b19f7076b38038ed0da55a1c474f35fb57`, passed
  all 12 routes and 36 CLI refusal assertions in 48.8 seconds. Each route used
  two fictional rows and five columns, with ordered typed readback, provenance,
  value-free responses, unchanged inputs and cleanup. Refusals cover stale
  snapshot digest, one-byte output cap and existing destination.
- Machine-readable receipt: [installed replay](installed-replay-2026-11-09.json).
  MCP coverage here calls the registered application function, not SDK stdio.
  SQL inputs use supplied fictional Arrow streams, not configured owned SQL
  sessions, live databases or worker/network acceptance. Output SQL is text only.
  All cells are explicit replacements; no preservation receipt was issued.

This closes a fresh small installed-artifact replay slice only. It is not the
1M × 100 capacity proof, human consent, an independent safety review or a claim
that twelve configured/public transport routes have passed at target size.

## 1. Target capacity: separate the missing proof from configurable defaults

Historical private fictional 12/12 input/output target measurements are complete.
The four input origins are CSV, Parquet, PostgreSQL result and Trino result;
each has CSV, Parquet and PostgreSQL SQL-text output. They do not establish
current installed public/common/configured-session acceptance at target size.

| Stage | Current enforcement | Remaining evidence |
| --- | --- | --- |
| Shape | `TransformationInputLimits`: 1,000,000 rows, 1,000 columns and 100,000,000 cells by default; positive signed-64-bit configurable fields | 1M × 100 is not blocked by the source-free generator's separate 100k default. Prove the actual bound fixture through selected public routes. |
| Input/output bytes | Default per-file 128 MiB, total/expanded/output 512 MiB; transformation session > explicit saved profile > legacy session > default; run caps may lower but not exceed effective ceilings | Historical fixtures include ~600 MB CSV and ~2.24 GB SQL text. Record explicit per-stage ceilings plus policy/mapping/control overhead; default-size rejection is correct, not grounds to remove caps. |
| CLI work | `GenerationBudget()` reads `TEST_DATA_AGENT_MAX_GENERATION_SECONDS` (default 300) | Record a sufficient finite budget and actual elapsed time; do not mistake historical explicitly supplied 1800/3600-second private budgets for CLI defaults. |
| MCP work | `TEST_DATA_AGENT_MCP_MAX_INVOCATION_SECONDS` defaults to 120; transport and application share the captured value, independent of generation/profiling budgets | Set each required finite deadline before server startup; prove actual SDK stdio execution and refusal/cleanup. Tool arguments cannot raise the request deadline. |
| Configured owned SQL session | Lifetime default 300 seconds, allowed 0.1–3600; lifetime allocation reservation default 64 MiB; reservation charges requested `max_total_bytes` before capture, is not refunded, and is separate from output cap | Account for capture, review, any genuine local approval, validation and execution within one non-renewable lifetime. Explicitly admit enough cumulative bytes; do not reset reservations or reconnect. |
| SQL capture | Administrator binding and transformation row/file limits checked before dedicated isolated capture; ordinary aggregate profiling limits stay separate | Exercise the configured loader/session and real worker composition using fictional drivers; supplied Arrow streams alone do not prove this route. No live source is needed or authorized. |

Code anchors: `core/transformation_limits.py`, `core/limits.py`,
`cli_transformation_candidate.py`, `mcp_transformation_candidate.py`,
`mcp_generator_server.py`, `io/transformation_query_workflow.py`,
`io/transformation_query_sessions.py` and `io/transformation_trino_stream.py`
under `src/test_data_agent/`. Operator settings are already documented in
[configuration](../../../docs/reference/configuration.md).

### Next capacity deliverable

Extend the existing opt-in acceptance harnesses rather than add another engine:

1. Add an explicit registered-execution option to the existing private scale
   harness, retaining full ordered readback, exact bytes/provenance and cleanup.
   First prove 2,051 × 3 (crosses the 1,024-row Parquet encoding boundary) through
   saved profile/CLI and genuine SDK stdio; retain every refusal case.
2. Add a separate configured-owned SQL fixture through the actual session loader
   and worker composition, with one frozen capture, no reconnect and expiry/
   admission/cleanup negatives. Inject only the fictional driver/endpoint boundary;
   never patch product policy, receipts, budgets or publication guards for a pass.
3. Record every stage's effective ceilings, source and harness identities,
   installed import, elapsed time, bytes, actual readback and worker cleanup.
   Validate the harness on small data before the costly 300k × 50 and 1M × 100
   executions. Run sequentially with bounded temporary storage, not twelve large
   concurrent jobs. Results apply only to measured shapes, widths and routes.
4. Reconcile the exact installed public/common/configured route matrix. Keep
   unsupported, unmeasured and historical cells explicit. Capacity does not add
   hard-RSS/native decoder isolation or exact network-byte guarantees.

No target-size campaign was launched by this audit. No evidence supports
raising global defaults, reusing the source-free scalable engine for mixed-origin
transformation, or describing the remaining task as another 12 private reruns.

## 2. Trust-boundary amendment: prepare a scoped evidence dossier

The accepted product decisions already exist. Do not ask the owner to reselect
ADR-0021's local operator model or ADR-0029's uniform replacement contract.
Do not infer a new policy decision from RC3 publication or its waived manual
synthetic-client check. The latter is not preservation or amendment approval.

| Contract | Current authoritative locations | Evidence/remaining reconciliation |
| --- | --- | --- |
| Separate mixed-origin surface; synthetic generation remains source-free | AGENTS.md, SECURITY.md, ADR-0020; baseline `safe-mcp-workflow` | Existing public registration is shipped. Historical prospective prose does not revoke it or authorize a new extension. |
| Direct preserve/fallback needs non-sensitive evidence, bounded comment, exact local TTY receipt; DECIMAL preserve remains blocked | AGENTS.md, SECURITY.md, ADR-0021; baseline `safe-mcp-workflow` | Receipt/snapshot/approval tests and historical genuine stable acceptance exist. Agents/MCP cannot issue approval; no fresh consent is inferred. |
| Explicit mapped permutations are replacements for all fields, with value-free sensitivity notes | AGENTS.md, SECURITY.md, ADR-0029; baseline `safe-mcp-workflow`; active transformation delta | Six current fictional sensitive-mapping tests cover two actions × three outputs. Membership is not preservation; actual mapped-cell evidence is required. |
| Broader transformation capability contract | Active `specs/selective-source-transformation/spec.md` delta | Its baseline currently contains only the separately archived scalar-null relationship requirement. Reconcile accepted shipped requirements explicitly; do not blindly copy historical/private/deferred requirements into the baseline. |
| Changed activation needs matching policy/contracts, executable evidence and independent exact-SHA review | AGENTS.md, SECURITY.md, safety-boundary.md, ADR-0029 | Old private/amendment reviews and broad release acceptance retain their scopes. They do not automatically close this separately recorded amendment task. |

### Next amendment deliverable and closure criteria

Prepare one narrow, reviewable documentary patch mapping existing accepted
shipped semantics across AGENTS.md, SECURITY.md, safety-model.md and the affected
baseline/active OpenSpec requirements. Identify each actual discrepancy and its
governing accepted decision; retain dated historical review reports unchanged.
The patch must not activate private derive, DECIMAL preserve, external callbacks,
source-row EAV pivot/unpivot, stronger human identity, different temporal-key
equality, source-free authority or broader SQL/data access. Those are separate
questions or excluded scope, not prerequisites for this reconciliation.

Bind the dossier to the finished immutable patch SHA, enumerate executable
positive/negative receipt, snapshot, mapping-evidence, workspace, disclosure,
budget and publication tests, and obtain an actual independent review of that
specific amendment scope. Label AI review honestly; never synthesize human or
GitHub approval. Only close the parent after the scoped disposition and required
checks are recorded. This audit is author analysis, not independent clearance.

## Follow-up execution

The installed wheel and environment above were reused. The harness and
configured worker tests are in `9251612aee87132ca32f54a5acd6eb37aef528d5`.
The new opt-in `scripts/accept_transformation_csv_scale.py` SHA-256 was
`08510430c19469869b013fd96c8cfb3e758c76540e7db023c5c235bfa614009c`.
For a small reproduction, run the script with the isolated installed Python
(`-I`), `--rows 2051 --columns 3 --output-format parquet --max-seconds 90`
and one of `--entrance private`, `--entrance cli` or `--entrance mcp`.

| Installed route | Ordered cells read back | Data bytes | End-to-end seconds | Refusals |
| --- | ---: | ---: | ---: | ---: |
| CSV → Parquet, private control | 6,153 | 2,034 | 0.299 | — |
| CSV → Parquet, registered CLI | 6,153 | 2,034 | 1.575 | 3 |
| CSV → Parquet, registered MCP SDK stdio | 6,153 | 2,034 | 1.996 | 3 |
| Parquet → PostgreSQL SQL text, registered MCP SDK stdio | 6,153 | 212,448 | 1.341 | 3 |

The runs used a 512 MiB harness budget. Both registered routes checked matching
review and execution digests, stale digest, one-byte output cap and existing
output; failures left the workspace and the existing artifact unchanged.
Success checked ordered typed content, replacement provenance, unchanged input
and scratch cleanup. The MCP client discovered review and execution and found
no receipt issuer. The harness checks that its fictional mapping literals do
not appear as quoted values in transport results or diagnostics. All runs are
replacement-only, use local files, and do not establish human consent. SQL
output was read back as text and never executed.

The installed registered CLI also passed CSV → CSV at 300,000 × 50 using
`--rows 300000 --columns 50 --output-format csv --max-seconds 1800 --entrance cli`
and the default 512 MiB byte budget. Profile completed at 38.351 s, saved review
at 75.990 s, and the full run at 455.275 s. The published CSV was 90,150,450
bytes; all 15,000,000 cells, all three refusals, input digest, provenance and
cleanup passed. Elapsed time includes setup, profile, repeated review/refusal
work and complete readback; it is not a standalone generation-time benchmark.
This is one installed intermediate-size route. Current public/common/configured
1M × 100 runs are still required; the private historical matrix is not repeated.

The configured PostgreSQL and Trino composition tests call the actual session
loader and spawned workers with only the fictional driver factories substituted.
For two inputs PostgreSQL opens four connections (metadata and read-only
capture per input); Trino opens six (column discovery, no-row inspection and
read-only capture per input). Both verify no reconnect on review/validate/execute,
exact ordered replacement outputs, summary-only responses and owned capture/worker
cleanup. These are small source-tree tests, not installed SDK stdio, live DB or
target-scale SQL evidence. The latest affected query/session/worker suites passed
88 tests, including the two configured composition cases. Existing admission
and expiry tests also ran in the earlier focused suite.

The trust amendment reconciles the shipped registration in the MCP baseline
and active deltas, and records the accepted narrow transformation contract in
its own baseline. SECURITY and the safety model align with those documents;
AGENTS already expresses the applicable safety constraints. The patch does
not change code, policy gates or the owner decisions in ADR-0021 and ADR-0029.
The scoped proof set includes activation-boundary, receipt/approval, exact
snapshot, unified mapping, MCP, configured-session, isolated PostgreSQL and
documentation tests: the initial run passed 209 and skipped six. The skipped terminal cases
are not new human or controlling-TTY evidence. Independent review of the
finished amendment is outstanding; neither parent task is checked off.
