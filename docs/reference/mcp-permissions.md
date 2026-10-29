# MCP Permissions

Use this reference to decide which MCP tools a client may call and which local
resources each server process needs. Start with the
[generator-only quickstart](../how-to/mcp.md#generator-only-quickstart).
The tables describe stable `1.6.0`; installed versions can
expose fewer tools. Check the installed version and its `tools/list` response.
Discovery is an inventory, not authorization to use a dataset or activate a
gated transformation extension.

## Who Grants Access

| Layer | Who configures it | What it controls |
| --- | --- | --- |
| MCP client | Client operator | Whether the assistant can discover/call a server's tools and when the client asks for confirmation. Use the client's tool allow/ask controls, if supported. |
| Operating system or container | Deployment administrator | Executable launch, readable inputs, writable outputs and temporary storage, readable secrets, and network destinations. Run as a dedicated non-root user. |
| Application configuration | Server administrator | Generator workspace, Trino allowlists, optional row-tool registration, and work/response budgets. Tool arguments cannot widen these settings. |
| Database | Database administrator | Authentication, metadata visibility, and read-only access to selected tables/columns. Application allowlists do not create database grants. |
| Workflow review | Human reviewer | Approval of the exact synthetic specification; separate local controlling-terminal approval for preservation. A client permission to call a tool does not supply either review. |

Both installed server commands use **stdio**. The client launches a local
process and exchanges MCP messages on its standard input/output. No listening
HTTP port, inbound firewall rule, remote MCP login, or MCP OAuth scope is
required. These entrypoints do not implement a remote authorization server or
publish per-tool OAuth scopes or permission annotations. Configure permissions
in the actual client and deployment; do not invent a `permissions` or `scopes`
key in the server configuration. Trino authentication is a separate outbound
database connection, not authentication of an MCP caller.

Client confirmation rules apply in that client. They do not restrict a different
client or grant an operating-system sandbox. The normal server does not provide
a configurable per-tool authorization list; `TRINO_ENABLE_SAFE_SELECT` controls
the separate optional row tool. For a hard isolation boundary, use dedicated
process credentials and the [separate container deployments](../operations/containers.md).

## Minimum Process Rights

| Workflow | Local read access | Local write access | Network and credentials |
| --- | --- | --- | --- |
| Synthetic generation | Installed runtime; selected input files, safe profiles, specs and rules inside one workspace | Workspace planning artifacts, new output bundles/reports, and bounded runtime temporary storage | No database or AI-provider credentials and no network are needed. |
| Default Trino profiling | Installed runtime and any administrator-selected TLS/authentication files | Runtime temporary storage; separate audit directory only if enabled | Outbound access to the configured Trino endpoint; a restricted read-only database identity. No generator workspace mount is needed. |
| Local selective transformation | Workspace source snapshots, policies, mappings, and any existing local receipt | New selected output bundle and owned temporary storage/cleanup | No database or provider connection is needed for local-file operations. Preservation requires separate local approval. |
| Configured SQL transformation session | Workspace batch profile, bounded query-reference/query files, policies/mappings; configured connection secrets | Private owned temporary captures/receipts and selected output bundle | Authorized PostgreSQL or Trino connection, optional adapter dependencies and read-only grants. This is a separate row-capture workflow, not aggregate-only profiling. |
| Optional audit logging, either server | The selected HMAC key or key file | Create/append the selected log in its existing private parent directory | No network required. Use different keys and directories for separate workers. |

`TEST_DATA_AGENT_WORKSPACE_ROOT` must point to an existing dedicated directory.
If unset, the generator uses its current working directory. Generator tool paths
must resolve below the root; relative paths are easiest to audit. Escapes through
existing symlinks are rejected. The setting restricts application tool paths;
it does not remove the process user's rights to other host files. Audit paths,
authentication files and owned runtime temporary storage have their own
administrator-configured locations and are not ordinary workspace tool paths.
Keep secrets outside the client-accessible workspace.

Grant read/traverse access to selected inputs and write/traverse access only to
the required workspace/output and temporary directories. The server must also
be able to remove its own temporary files. Root, sudo, access to the user's
whole home directory, and a Docker socket inside the worker are unnecessary.
The normal MCP generation tools refuse existing output files and non-empty
output folders; they have no folder-overwrite argument. CLI `--overwrite` does
not grant MCP overwrite permission.

The shipped generator Compose service has no network or database dependencies.
Keep that setup for synthetic/local-file work. It cannot perform configured SQL
capture; that separately accepted workflow needs an explicitly provisioned
deployment, not a silent change to the generator-only setup.

## Generator Tool Rights

All file references below are workspace-confined, except the server-owned
temporary session storage described above. Responses contain summaries, reports
and artifact paths, never source or generated rows or mapping literals.
An enabled audit log adds one started/terminal record to every invocation,
including otherwise read-only tools.

| Tool | Reads | Writes or other effects | Review requirement |
| --- | --- | --- | --- |
| `profile_csv` | Selected CSV | New safe aggregate profile JSON | No generation approval; authorize profiling of the selected input. |
| `infer_dataset_spec` | Safe profile file or bounded inline profile | New specification | Proposal only; no generation. |
| `plan_dataset` | CSV, CSV folder, or safe profile | New planning directory, profile, spec and plan artifacts | Stops before generation for human review. |
| `plan_trino_dataset` | Bounded safe Trino profile payload | New planning directory and spec/plan artifacts | Stops for review; this tool makes no database connection. |
| `inspect_dataset_plan` | Existing plan, spec and completion artifacts | None, apart from optional audit | Read-only inspection; returns the current spec fingerprint. |
| `approve_dataset_plan` | Existing plan and exact current spec | Synthetic output, validation, manifest, approval/completion artifacts | Human must review and approve the exact `reviewed_spec_sha256` first; stale fingerprints reject. |
| `recover_dataset_plan` | Existing interrupted plan and published bundle | Recovery/completion artifacts | Reuses the human-reviewed fingerprint; revalidates, never regenerates rows. |
| `generate_dataset` | Reviewed spec and embedded/file/inline business rules | New synthetic bundle, validation and manifest | Lower-level direct generation: no planning approval argument. Require client/operator approval before granting this call. |
| `export_dataset` | Reviewed spec and rules | Fresh synthetic bundle in the requested format | Same direct-generation review policy; not conversion/export of arbitrary source rows. |
| `validate_dataset` | Spec and generated bundle with matching manifest | New report only when `output_path` is supplied | No generation approval; omit `output_path` for inspection without a new report file. |
| `review_transformation` | Fixed local source, policy and referenced mappings | None, apart from optional audit | Review only; cannot issue a preservation receipt or execute. |
| `execute_transformation` | Exact reviewed local snapshot, policy/mappings and any required existing receipt | New labelled mixed-origin bundle and temporary work | Requires `snapshot_sha256`; preservation additionally needs a matching human local-CLI receipt. |
| `common_transformation` | Saved batch profile and its local inputs/policies/mappings | `review`: no retained output; `validate`: temporary output; `execute`: temporary output or new selected destination | Validate/execute bind the exact digest; preservation consumes an existing local receipt. Cannot issue approval. |
| `configured_query_session` | Batch profile, bounded SQL references and configured database on `open`; frozen captures afterward | Owned temporary captures; `execute` publishes selected output; `close`, expiry and shutdown clean up | `open` needs separate database authority. Validate/execute bind the digest; preservation consumes local approval. Review/validate/execute never reconnect. |

The generator **console entrypoint** injects a workspace and session owner and
registers all 14 tools above. The module-level SDK object has only the 12 base
tools; `common_transformation` and `configured_query_session` need explicit
runtime ownership when embedded. Do not use a shorter SDK inventory as the
console server's permission list. The two extensions retain their separate
activation/release acceptance gates; registration or a documentation example
does not authorize private data access. See the
[transformation and SQL-session workflow](../how-to/mcp.md#configured-sql-sessions-16-rc).

Synthetic planning approval and preservation approval are different contracts.
The synthetic workflow checks a reviewed spec fingerprint and writes its own
generation receipt; it cannot prove that a human actually read the spec. The
client must obtain that review before calling approval. Advanced direct
generation tools do not enforce this planning sequence. Do not automatically
allow them to bypass the review-first client policy.

Resuming an existing client conversation adds no rights. Restore its existing
workspace, installation, connection and narrow tool policy, then
[inspect the saved plan and review the full current specification](../how-to/mcp.md#resume-an-existing-synthetic-plan)
before new dataset consent. Client tool prompts, operating-system access and
dataset review remain separate; an earlier consent phrase or successful resume
preflight does not establish current-specification review.

Preservation receipts must be issued by the separate human local CLI through
its controlling terminal. MCP has no preservation approval tool or `approved`
boolean. A hash, tool-call confirmation or database grant cannot replace the
matching receipt. Changed source/policy/mapping bytes invalidate it. Explicit
mapped replacement retains its separate reviewed contract and is not an
implicit preservation or source-copy fallback.

## Trino Tool Rights

The default aggregate-only tools return metadata and aggregates. The explicit
opt-in `run_safe_select` is a separate row-returning surface with different
disclosure risks and is unnecessary for planning synthetic data.

Give the Trino identity only the metadata visibility and SELECT access needed
for the selected dataset. Configure grants in the actual Trino access-control
system and underlying connector; there is no universal GRANT script for every
backend. None of these tools needs DDL, DML, ownership, role administration or
grant-option rights. Database grants remain necessary even when application
allowlists are configured.

| Tool | Database work | Response / additional permission |
| --- | --- | --- |
| `list_catalogs` | Catalog discovery | Only catalog names admitted by the catalog allowlist. |
| `list_schemas` | Schema discovery in an allowed catalog | Only schema names admitted by the schema allowlist. |
| `list_tables` | Table discovery in an allowed catalog/schema | Table names visible to the database identity; column selectors do not filter this list. |
| `describe_table` | Column metadata in an allowed catalog/schema | Visible column names/types; column selectors do not filter this response. |
| `profile_table` | Aggregate count for one table | Count only. |
| `profile_column` | Cardinality/null aggregates for one column | Aggregate counts, not source rows. |
| `profile_table_safe` | Selected column profiles and table count | Bounded aggregate profile, synthetic category labels/masked patterns; no source rows. |
| `profile_foreign_key` | Parent/child key relationship aggregates | Counts/confidence; needs read access to both tables and key columns. |
| `profile_temporal_ordering` | Ordering aggregates | Counts/confidence; needs both temporal columns. |
| `profile_formula_rule` | Formula residual aggregates | Counts/confidence; needs target and all operand columns. |
| `profile_conditional_required` | Conditional null-check aggregates | Counts/confidence; needs condition and target columns. |
| `profile_conditional_allowed_values` | Conditional membership aggregates | Counts/confidence; use only reviewed non-sensitive rule literals. |
| `profile_aggregate_mapping` | Parent/child aggregate comparison | Counts/confidence; needs both tables, keys and measure columns. |
| `run_safe_select` | Bounded validated read-only SELECT | **Optional row-returning tool**, absent unless `TRINO_ENABLE_SAFE_SELECT=true`. Strings and recognized sensitive values are masked; other source values may remain. Never use its rows as generated data or relay them to an LLM. |

`TRINO_ALLOWED_CATALOGS` and `TRINO_ALLOWED_SCHEMAS` are required by default.
They are independent sets, not catalog/schema pairs: with two values in each,
each catalog can admit both schemas. Use narrow values and database grants when
different catalogs require different access.

`TRINO_ALLOWED_TABLE_COLUMNS` narrows column selection for `profile_table_safe`.
It is **not a universal per-tool ACL**: metadata discovery, count/cardinality
tools, rule probes and optional `run_safe_select` do not enforce these selectors.
The optional row tool checks catalog/schema scope and SQL safety, not this
column list. Enforce strict table/column visibility through the database
identity, and limit callable tools in the client. Table-qualified
`catalog.schema.table.*` expands bounded metadata for safe profiling; it is not
an unrestricted SQL projection or permission to disclose raw categories.
Default aggregate profiling substitutes synthetic category labels or masked
patterns. Raw category queries are internal bounded work, not row disclosure.

For example, these application settings select two columns for safe table
profiling; the database administrator must separately restrict the reader:

```json
{
  "TRINO_ALLOWED_CATALOGS": "hive",
  "TRINO_ALLOWED_SCHEMAS": "test_data",
  "TRINO_ALLOWED_TABLE_COLUMNS": "hive.test_data.customers.customer_id,hive.test_data.customers.status",
  "TRINO_ENABLE_SAFE_SELECT": "false"
}
```

Place these values in the Trino server's `env` alongside its verified HTTPS
endpoint and runtime authentication settings, as shown in
[client configuration](../how-to/mcp.md#mcp-client-configuration).
Missing/denied rights should be resolved by narrowing the request or having the
administrator grant the selected read access, not by enabling
`TRINO_ALLOW_UNRESTRICTED` or `TRINO_ALLOW_INSECURE_HTTP`.
See [configuration](configuration.md#trino-connection) for authentication and
[invocation limits](configuration.md#trino-invocation-limits); a larger budget
does not grant access to more data.

## Choose A Client Policy And Check It

For the review-first synthetic workflow, enable `plan_dataset` (or
`plan_trino_dataset`) and `inspect_dataset_plan`; require explicit human review
before `approve_dataset_plan`. Allow `recover_dataset_plan` only with that same
reviewed fingerprint and the recovery state reported by inspection. Add
`profile_csv`, `infer_dataset_spec`, `validate_dataset` and direct generation
only as the workflow needs them. Keep transformation and optional row tools
outside a synthetic-only client's callable set. Apply these choices using the
client's supported settings; the table is not a server configuration format.

Before using the connection:

1. Check the installed package version and `tools/list`; compare names with
   the tables, including startup-only and optional tools.
2. With a fictional fixture, run the
   [planning/inspection/approval quickstart](../how-to/mcp.md#generator-only-quickstart).
   Confirm no generated dataset exists before approval and outputs stay inside
   the selected workspace.
3. For an independently authorized database, verify discovery and safe profiling
   using its restricted reader. Confirm an excluded catalog/schema is refused;
   do not infer table/column isolation from the column-selector setting alone.
4. Confirm default Trino discovery omits `run_safe_select`; verify only summaries
   and artifact paths reach the assistant. Keep credentials and raw files out
   of chat, prompts and committed client configuration.

If a tool is missing, check version, installed extras, runtime composition and
client tool policy. For filesystem refusal, check the narrow root, existing
destination and process ownership. For database refusal, check both allowlists
and database grants. Audit admission and resource-budget refusals require their
own fixes; they are not permission to expand data access. See
[audit setup](../operations/audit-logging.md) and the
[MCP recovery guide](../how-to/mcp.md#corrective-next-steps).

The assistant client itself may use an external model provider under its own
policy. These MCP servers do not need OpenAI/GigaChat API credentials for the
workflows above and expose no advisor tool. Provider integration, shell/CLI
access and arbitrary file-reading tools are separate capabilities with their
own permissions; enabling MCP does not grant or constrain them.

The finite stable 1.6.0 campaign completed with
[recorded coverage and limits](../release-evidence-1.6.0.md). Candidate 1.7.0rc1
has separate [installed-interface evidence](../release-evidence-1.7.0rc1.md).
The [acceptance matrix](../acceptance-matrix.md) also contains historical and
remaining targets; it does not establish new live database, client UI,
preservation approval or all-route capacity acceptance.
