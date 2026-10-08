# Connect An MCP Client

The project exposes two MCP servers with separate trust boundaries:

- the generator server reads and writes only inside one workspace;
- the Trino server's default aggregate-only tools provide allowlisted,
  read-only metadata and profiling.

Start with the generator server. Add Trino only when database profiling is
required.

For process and dependency isolation, use the separate hardened images in
[Container Deployment](../operations/containers.md). The generator example has
no network, while the Trino worker receives no generator workspace mount.

## Generator-Only Quickstart

Install the optional MCP support in a dedicated environment. Use the version
selected in [Installation](../getting-started/installation.md); for a candidate,
install its reviewed wheel instead of assuming it is already published.

```bash
python3 -m venv /path/to/mcp-env
/path/to/mcp-env/bin/python -m pip install "agent-paranoid-android[mcp]"
mkdir -p /path/to/synthetic-workspace
```

Desktop clients may not inherit your shell's PATH. Configure the absolute
executable path and restart the client after changing its configuration:

```json
{
  "mcpServers": {
    "test-data-agent-generator": {
      "command": "/path/to/mcp-env/bin/test-data-agent-mcp-generator",
      "env": {
        "TEST_DATA_AGENT_WORKSPACE_ROOT": "/path/to/synthetic-workspace"
      }
    }
  }
}
```

Replace both absolute paths with your own. The client should discover
`plan_dataset`, `inspect_dataset_plan`, `approve_dataset_plan`, and
`recover_dataset_plan`. This local workflow requires no database or AI-provider
credentials. The `mcpServers` example applies to clients supporting that
configuration format; use your client's equivalent server settings otherwise.

Create `customers.csv` inside the workspace with this fictional fixture:

```csv
customer_id,email,status
1,alice@example.com,active
2,bob@example.com,paused
```

Ask your assistant: "Plan four synthetic customers from customers.csv with seed
81. Show me the specification for review before generating files."
The corresponding `plan_dataset` arguments are:

```json
{
  "source_path": "customers.csv",
  "workspace_path": "agent/customers",
  "source_type": "csv",
  "count": 4,
  "seed": 81,
  "output_format": "csv",
  "table_name": "customers"
}
```

The response has `approval_required: true` and `spec_path`. No generated dataset
exists yet. Open the spec artifact locally and review field types, privacy,
relationships, count, and seed. Inspection is a read-only operation:

```json
{"workspace_path": "agent/customers"}
```

Call `inspect_dataset_plan` with those arguments. After a human reviews and
explicitly approves the exact current specification, call
`approve_dataset_plan` with:

```json
{
  "workspace_path": "agent/customers",
  "reviewed_spec_sha256": "<review.current_spec_sha256 from inspection>"
}
```

Replace the placeholder with the actual fingerprint. If the specification
changes, inspect and review it again; a copied fingerprint is not human approval.
The approval response should report `row_counts: {"customers": 4}`,
`validation_valid: true`, and paths to output, manifest, validation report, and
approval receipt. Inspect the same workspace again to confirm `phase: completed`.
Report these summaries and paths; do not attach or inline dataset rows.

### Corrective Next Steps

- Missing executable or MCP extra: check the absolute path, install `[mcp]`
  into that environment, and restart the client.
- Rejected workspace path: move the input inside the configured root and use
  relative paths. Do not expand permissions to bypass the boundary.
- Non-empty planning directory: select a new workspace; inspect an existing
  plan instead of overwriting it.
- Stale review fingerprint: inspect, review the changed specification, and
  obtain renewed human approval before submitting its current fingerprint.
- Interrupted approval or a lost response: inspect first. If `phase` is
  `completed`, report the existing result. If `next_action` is `recover`, call
  `recover_dataset_plan` with the workspace and reviewed fingerprint. Recovery
  retains published outputs without generating another dataset. If inspection
  requests review and approval, follow that state instead.
- Fixed argument-validation or transport-limit error: correct arguments against
  the discovered tool schema or reduce request size. Do not disable budgets or
  expect rejected values to be reflected in error messages.

Add Trino only for database profiling, using the separate configuration and
[Safe Trino Sequence](#safe-trino-sequence) below. Do not give the generator
server database credentials.

## Prepare A Workspace

### Closed Common-Profile Candidate

The 1.6 RC runtime adds `common_transformation` to the generator server.
Published 1.5.0 does not include this tool; registration is not release clearance.
It accepts `operation` (`review`, `validate`, `execute`), workspace-relative
`profile`, and positive explicit `max_total_bytes`, `max_review_bytes`,
`max_output_bytes`. Validation/execution require the exact reviewed
`snapshot_sha256`. Preservation additionally requires a pre-existing local
`receipt`; MCP cannot issue it. Optional `destination` is execute-only and names
a new direct-child output bundle. Without it, execution is temporary.

The workspace root comes from server configuration, never tool arguments.
Responses contain value-free review/summary metadata, not output rows or mapping
literals. Existing transport/work budgets still apply; these byte settings do
not enlarge source-free profiling or serialized response budgets. Unknown
arguments, including `root` and `approved`, are rejected without reflection.
Configuration creation and human confirmation remain local CLI operations.
Installed fictional acceptance with MCP SDK1/SDK2 is evidence for this candidate,
not permission to activate it or process private data.

```bash
mkdir -p /path/to/synthetic-workspace
```

Inputs, safe profiles, reviewed specs, rules, and outputs used through generator
MCP tools must remain below this directory.

## MCP Client Configuration

Use the installed console commands:

```json
{
  "mcpServers": {
    "test-data-agent-generator": {
      "command": "test-data-agent-mcp-generator",
      "env": {
        "TEST_DATA_AGENT_WORKSPACE_ROOT": "/path/to/synthetic-workspace",
        "TEST_DATA_AGENT_MCP_MAX_INVOCATION_SECONDS": "120"
      }
    },
    "test-data-agent-trino": {
      "command": "test-data-agent-mcp-trino",
      "env": {
        "TRINO_HOST": "trino.example.internal",
        "TRINO_PORT": "443",
        "TRINO_USER": "synthetic_data_reader",
        "TRINO_HTTP_SCHEME": "https",
        "TRINO_ALLOWED_CATALOGS": "hive,iceberg",
        "TRINO_ALLOWED_SCHEMAS": "test_data,staging",
        "TRINO_QUERY_MAX_EXECUTION_TIME": "30s",
        "TRINO_QUERY_MAX_RUN_TIME": "45s",
        "TRINO_QUERY_MAX_SCAN_PHYSICAL_BYTES": "1GB"
      }
    }
  }
}
```

Do not place a password or token directly in a committed MCP configuration.
Use the client's secret mechanism or an environment injected by the runtime.

## Safe Generator Sequence

For selective transformation review, call `review_transformation` with
workspace-relative `input_path`, `policy_path` and optional `table_name`.
It reads a fixed local snapshot in the format selected by the saved policy and
returns `review_only`, `snapshot_sha256` and the same value-free review as CLI
`transform-review`. Referenced mapping files stay local to the policy directory.
The tool writes no artifacts, creates no approval receipt, executes no
transformation and connects to no database. Public transformation execution
remains gated; normal generator operations below remain source-free.

The isolated activation candidate additionally registers `execute_transformation`
with workspace-relative `input_path`, `policy_path`, new `output_path`, mandatory
`snapshot_sha256`, optional `table_name`/existing `receipt_path`, and optional
`max_total_input_bytes`/`max_output_bytes` run caps. It consumes the same exact
snapshots and budgets as CLI execution and returns `transformation_completed`,
digest, provenance and budget summaries, never dataset rows or mapping literals.
Explicit replacements may permute sensitive source values under the same
field-independent contract. Review retains a value-free sensitivity note;
mapped values stay in the selected local artifact, never MCP responses. This
does not grant direct preservation or an implicit copy fallback.

Preservation requires a matching receipt issued separately by the human local
controlling-terminal CLI. There is no MCP receipt issuer or approval flag.
Changed inputs invalidate receipts; workspace escapes, existing destinations,
unsupported actions and budget violations fail closed without copying fallback.
This isolated candidate registers the consumer; the released 1.5.0 package
does not. Public delivery requires installed acceptance, matching safety/spec
documentation and independent exact-SHA safety review. A receipt never
authorizes database access or external APIs.

1. Put a CSV file, CSV folder, or safe profile below the workspace root.
2. Call `plan_dataset` with that source, a new agent workspace, count, seed,
   and output format.
3. Stop and review the written `dataset_spec.yaml`.
4. Call `inspect_dataset_plan` and record
   `review.current_spec_sha256`.
5. Call `approve_dataset_plan` with that exact fingerprint only after review.
6. Report summaries and artifact paths, not generated rows.

Use `profile_csv`, `infer_dataset_spec`, `generate_dataset`, and
`validate_dataset` separately when an advanced client needs control over each
pipeline stage.

For business rules, provide exactly one of `business_rules_path` or a bounded
structured `business_rules_payload`.

Generator MCP reads newline-framed requests through the same bounded transport
used by Trino MCP. Each request receives a fresh non-resettable budget. The
default boundary rejects raw frames above 1 MiB, JSON deeper than 100 levels,
JSON with more than 10,000 structural nodes, or an individual scalar above
256 KiB before MCP/Pydantic materialization. Complete JSON-RPC responses are
limited to 4 MiB and overflow becomes a fixed local error.
Typed argument-validation failures also become the fixed
`Tool arguments failed validation` error; rejected caller values and nested
Pydantic diagnostics are not returned.
Malformed typed requests are rejected before SDK dispatch with fixed
`Invalid request parameters` text, and malformed notifications are dropped;
their caller-controlled values do not enter SDK logs or retained exceptions.
Each server process admits at most 32 active requests. Excess requests receive
a fixed bounded capacity error, and disconnect or teardown clears retained
request state. Trino execution is separately capped at eight concurrent
operations per process.

## Safe Trino Sequence

The default aggregate-only tools are source-literal-free and contain only
metadata and aggregate profiling operations:

- `list_catalogs`, `list_schemas`, `list_tables`, `describe_table`;
- `profile_table`, `profile_table_safe`, `profile_column`;
- `profile_foreign_key`, `profile_temporal_ordering`, `profile_formula_rule`;
- `profile_conditional_required`, `profile_conditional_allowed_values`;
- `profile_aggregate_mapping`.

Catalog and schema discovery returns only names present in the configured
allowlists. Tables may be listed only after their catalog and schema pass those
allowlists. Backend-controlled driver and enumeration failures are exposed as
the fixed `Trino request failed` error without retaining the original text.

This default aggregate-only surface has no row-returning diagnostic. Its
successful responses, validation and database errors, and metadata-only audit
records do not contain source-cell literals.

1. Call `list_catalogs`, `list_schemas`, and `list_tables`.
2. Call `describe_table`.
3. Call `profile_table_safe` for an allowlisted table.
4. Pass that response to generator `plan_trino_dataset` with a new workspace,
   explicit count, seed, and output format.
5. Stop and review the written `dataset_spec.yaml`.
6. Call `inspect_dataset_plan` and record `review.current_spec_sha256`.
7. Call `approve_dataset_plan` with that value as `reviewed_spec_sha256` only
   after the human reviewed that exact spec fingerprint.
8. Do not export or relay source rows.

Both catalog and schema allowlists are mandatory by default. HTTPS is the
default. Plain HTTP requires an explicit override and is intended only for an
isolated local Trino instance.

The explicit opt-in row-returning tool `run_safe_select` is not exposed by
default. Trusted clients that need it must set `TRINO_ENABLE_SAFE_SELECT=true`.
The review-first planning sequence above does not require it. Its bounded
row-shaped result masks every string, including names and addresses missed by
heuristic classification, plus non-string fields or values recognized as
sensitive. Other non-string source values may remain, so enabling it does not
make returned rows source-free, anonymous, or suitable for relay to an LLM or
generated output.

## Expected Result

The default generator and default aggregate-only Trino tools return compact
metadata:

```text
rows: customers=25, orders=25
seed: 12345
validation: passed
synthetic: true
source rows copied: false
```

Generated files stay in the workspace. These default tools do not return
dataset or source rows; explicit opt-in row-returning tools are outside this
expected result.

## Failure Conditions

The server rejects:

- paths outside the workspace, including existing symlink escapes;
- existing output files and non-empty output directories;
- unrestricted SQL, DDL, DML, joins, CTEs, and subqueries;
- likely PII projections and raw sensitive rule literals;
- non-Trino or oversized inline planning profiles;
- DatasetSpec input passed to `plan_dataset` instead of `generate_dataset`;
- missing Trino allowlists;
- requests exceeding configured input, output, query, or execution limits.

See [MCP Tools](../mcp_examples.md) and
[Configuration](../reference/configuration.md) for details.

Preservation approval is never an MCP capability. This candidate's separate
workspace execution consumer cannot issue local receipts, return rows or
broaden source-free generator authority. Public delivery still requires the
scoped safety review and executable evidence specified by ADR-0020 and ADR-0021.


## Configured SQL Sessions (1.6 RC)

The running generator server registers `configured_query_session` with an
instance-owned session manager. Use only an authorized administrator-configured
PostgreSQL or Trino source. A saved batch profile and
[bounded query references](../reference/cli.md#configured-sql-sessions-16-rc)
are workspace files; tool arguments never select endpoints or credentials.

| Operation | Arguments | Result and lifetime |
| --- | --- | --- |
| `open` | `profile`, `references`, positive `max_total_bytes`, `max_review_bytes`, `max_output_bytes` | Capture once; return metadata review, opaque `handle`, digest, expiry and local approval descriptor. |
| `review` | `handle` | Reuse the same frozen batch; no database reconnection. |
| `validate` | `handle`, exact `snapshot_sha256` | Validate temporary output; retain the session until expiry or close. |
| `execute` | `handle`, exact `snapshot_sha256`, new direct-child `destination` | Verify any required local receipt, validate and publish; close the session. |
| `close` | `handle` | Remove owned snapshots and receipts; the handle cannot be reused. |

Responses contain review/summary metadata, never captured rows, query text,
mapping literals or connection secrets. `local_approval` contains an owned
temporary root, `batch.yaml`, a fixed receipt filename, digest and input/review
limits. These references help the local operator invoke the existing CLI:

```bash
test-data-agent transform-batch approve /owned/root batch.yaml local-session-receipt.json \
  --snapshot-sha256 REVIEWED_DIGEST \
  --max-total-input-bytes REVIEWED_INPUT_LIMIT --max-review-bytes REVIEWED_REVIEW_LIMIT
```

Use the exact metadata values while the session is alive. The CLI opens the
controlling terminal for confirmation; MCP has no approval operation or boolean.
This descriptor itself grants no authority. Direct or fallback preservation
requires a valid exact receipt; explicit mappings retain their separate safety
checks. Changed local bytes cannot produce a receipt for the frozen batch.

Expiry, refusal and shutdown remove owned inputs and receipts. Execution retains
only the selected validated output bundle inside the parent workspace. Expired
or closed handles refuse without silently recapturing. Start a new explicit
session and review its new digest if another capture is needed. Cumulative byte
admission is not refunded on close or failure; restart the owning server only
after resolving the refusal and reviewing its configured limits.

Cleanup failure returns a fixed incomplete-cleanup error and latches the owner
unhealthy; further work refuses. Preserve the failure evidence and inspect local
temporary storage before restarting. Default bounds and overrides are documented
in [configuration](../reference/configuration.md#configured-sql-session-bounds-16-rc).
The entrypoint closes all sessions in a shutdown handler even if transport fails.
Custom SDK embedding must explicitly inject a session owner and close it; the
module-level SDK object creates no SQL sessions.
