# Final Acceptance Matrix Plan

**Status: execution in progress; final acceptance remains open.** Run after the current feedback corrections,
source/output parity and MCP documentation are finished, before declaring their
combined result accepted or preparing the next release. The implementation
agent owns preparation and execution; actual human review remains the operator's
step. Track completion in OpenSpec change `cross-interface-acceptance`.

Existing successful tests are a starting point. They do not establish completed
acceptance of all interfaces, options or a later commit.

## Executable campaign

`scripts/accept_cross_interface_matrix.py` runs the 600 logical handoff cells
against an installed wheel, with two seeded repeats per cell. Supply the isolated
interpreter, installed package directory, exact candidate SHA and a new evidence
JSON path. Its worker must complete successfully and reap the MCP server before
the controller accepts the result. Bind the externally supplied SHA to the actual
wheel/sdist hashes in the final evidence; a package path alone is not that proof.

Acquisition is prepared once per route and an independently authored reviewed
specification then exercises shared generation semantics. Database aggregates in
this matrix are fictional stand-ins. Separate disposable PostgreSQL and Trino
integration runs establish live acquisition; the 600 cells do not represent 600
independent live profiling/inference runs.

`tests/test_acceptance_option_pairs.py` defines a finite covering array over nine
representative option axes, with explicit compatibility constraints. Its current
52 behavioral cases cover all 464 feasible pairs among 18,560 feasible
combinations. The ledger records its chosen values and limits. It does not claim
all values of every model property or all triples. Boundary, option-family,
all-rule-family, publication and safety cases live in the companion
`test_acceptance_option_families.py`, `test_acceptance_option_interactions.py` and
`test_negative_rule_overlap.py` suites. The lexical property/flag inventory is
navigation evidence, not a behavioral coverage measurement. Retained metadata
such as identifier prefixes is distinguished from effective generation controls.

`scripts/accept_container_workloads.py` runs actual hardened CLI/stdio workloads;
the container workflow saves their evidence for all three targets on both
architectures. The CI PostgreSQL and Trino jobs exercise fictional restricted
readers independently of the aggregate stand-ins. Record their exact SHA,
dependency versions and real versus emulated architecture in the final ledger.

## Coverage and sequence

| Stage | Required scope | Existing foundation / remaining work |
| --- | --- | --- |
| 0. Freeze inventory | One final SHA, wheel/sdist hashes, versions, source routes, schemas/options, public Python API, CLI parser, actual MCP `tools/list` | Contract fixtures and installed-package checks exist; create the expected case ledger and map coverage before running. |
| 1. Common contract | All 10 source routes × 4 outputs × 5 modes; all seven field types | `test_source_output_matrix.py` already has 200 core cases. Rerun on the final build; add the options/rules below. |
| 2. Installed interfaces | The same 200 logical compositions through each of Python, CLI and real stdio MCP | Target 600 logical cells at the current inventory. Existing Python/source tests and selected CLI/MCP parity cases do not prove this whole layer. |
| 3. Options and rules | Every public option/family; defaults, boundaries, invalid requests, compatible pairs and targeted interactions | Reuse rule, scalar, mode and publication suites; add missing cross-interface cases, not only more snapshots. |
| 4. Trust boundaries | Tool effects, approvals, paths, DB grants, SQL policy, secrets/redaction, audit, budgets, failure/recovery and cleanup | Existing direct-service, transport and safety suites; add installed-process and deployment evidence. |
| 5. Environments | Supported Python/dependency profiles, installed extras, MCP 1/2, three container targets on both architectures | Existing CI covers many profiles and container health. Actual container workloads and the complete acceptance ledger remain required. |
| 6. Acquisition and transformation | Disposable fictional PostgreSQL/Trino end-to-end acquisition; separate local/transformation session gates | Mocked DB aggregates are not live acquisition evidence. Keep preservation authority and mixed-origin outputs separate from synthetic generation. |
| 7. Evidence | Actual assistant-client run, human review, final coverage report, clean rerun after repairs | Close only when all required cases pass on the exact final SHA; release acceptance remains separate. |

The ten routes are those in the [source/output matrix](reference/source-output-matrix.md).
The four outputs are CSV, JSON, Parquet and generated SQL INSERT bundles. The
five modes are valid, edge, load_test, mixed and negative. Expected counts must
be regenerated from the final inventory; MCP compatibility repetitions are
environment runs, not additional logical source/output cells.

## Use the real interface contracts

- **Python:** verify documented public imports and generation/artifact APIs
  against the installed wheel, not only an editable checkout.
- **CLI:** use installed subprocesses, actual profiling/inference commands and
  reviewed YAML/JSON specs. Check JSON stdout, stderr/exit contracts, help,
  retained aliases and override precedence. Remove source-tree import paths.
- **MCP:** call installed entrypoints through a real stdio client, not imported
  helper functions. Exercise both supported SDK major versions. For source
  routes without an MCP profiler, explicitly prepare safe metadata outside MCP,
  then pass it through the supported profile/spec handoff. Never substitute raw
  row conversion for the generation transition.
- **Planning/agent workflow:** test plan → inspect → actual review → approve →
  completion, stale fingerprints, edited specs, interruption and recovery.
  Automated fictional approval fixtures and actual manual acceptance are
  different evidence.

`plan_dataset` has narrower convenience arguments: sources csv/csv-folder/profile,
formats csv/json/parquet and modes valid/negative/mixed. MCP generation/export
can consume a reviewed DatasetSpec carrying edge/load_test, SQL output, locale,
load multiplier and embedded business rules. Do not invent planning-tool flags
or silently drop those settings. Record any wrapper limitation and its tested
supported route; missing common generation semantics is a failure.

MCP has no overwrite argument. Test its existing-destination refusal. Test CLI
folder `--overwrite` separately for success, rollback and interruption. Provider
advisors have no MCP tool: test their actual Python/CLI contracts with fictional
transports and no external provider call.

## Option and rule inventory

Use the final typed schemas and discovery/parser inventories as the checklist,
including nested properties. Each accepted option needs omitted/default and
non-default behavior, applicable minimum/maximum and just-outside-invalid values,
plus explicit conflict/unsupported-type cases. Cover every compatible option
pair; list incompatible pairs and verify rejection. Continuous values and
arbitrary formulas cannot be an exhaustive Cartesian product.

| Family | Required cases |
| --- | --- |
| Fields | integer, float, decimal, boolean, string, date, datetime; nullable/null ratios including 0/1, semantic type, sensitivity, identifiers and independent key domains. |
| Distributions | synthetic_identifier, masked_patterns, numeric, decimal_range, numeric_shape, boolean, date_range, datetime_range, categorical, string_pattern; every declared option and compatible field type, malformed bounds/weights/shapes, decimal precision/scale. |
| Generation | Explicit seed/replay and seed bounds; locale; entity counts and explicit overrides; all modes; invalid ratios; default ×10 load and custom multiplier; exact explicit count; numeric scale_factor. |
| Validation and privacy | Every validation toggle and fail_fast; mandatory privacy/schema/constraint/business enforcement where required; privacy rules/settings, sensitive names/content and declared numeric-measure vetoes. |
| Relationships/native constraints | Every relationship/constraint type and status, active versus declared counts, missing references, incompatible fields, null/empty keys, cardinality, independent tables, formula/conditional/temporal/aggregate semantics. |
| Business rules | Field bounds/required/allowed values, conditions including null/ranges, temporal ordering, formula assign/check, assignment audit, FK, aggregates, scenarios/weights and exact comparison tolerance. |
| Rule delivery | Embedded DatasetSpec, external rule file and bounded MCP payload; equivalent effective contract, one application, conflict refusal and standalone reload validation. |
| Artifacts/I/O | All outputs reread and revalidate; null versus empty text, boolean/date operands, exact DECIMAL, wide integers, timestamp offsets, CSV escaping/spreadsheet inertness, marked Parquet scalars, custom filenames/entity mappings, legacy unmarked bundles. |

Run every business-rule family across all four outputs and Python/CLI/MCP through
the reviewed specification. Add explicit high-risk interactions beyond pairwise:

- DECIMAL × assign/check/aggregate rounding × serialization/revalidation.
- FK/cardinality × load_test multiplier × explicit count override.
- Null/empty text × conditional rules × CSV/Parquet round trip.
- Privacy classification × categories/numeric_measure × interface/report toggles.
- Mixed/negative × overlapping rules × expected-versus-unexpected failures.
- Business-rule delivery × native constraints × validation toggles.
- Multi-entity profiles × custom artifact names × overwrite/publication failure.

## Verify outcomes, not only successful exits

For every applicable successful cell, compare effective spec/rule fingerprints,
typed restored values, entity counts, relationships, mode, seed, validation
sections and manifest provenance. Re-run the same explicit seed in the same
environment. Normalize only declared volatile paths/timestamps; do not normalize
away decimal precision, invalid cells or meaningful report differences. Do not
claim byte identity between different dependency/runtime environments.

Valid/edge/load cases must satisfy their reviewed contract. Negative/mixed cases
must retain intended invalid cells through every output and report the expected
rule failures honestly. They must not become valid because an adapter repaired
values or validation was omitted. Unexpected additional violations fail the
case. Synthetic bundles must report synthetic provenance with no source-row
reuse; use fictional sentinel checks and actual logical comparison, not the
manifest flag alone. SQL reload must never execute SQL.

## Permission, failure and recovery campaign

Use the [MCP rights inventory](reference/mcp-permissions.md) as the per-tool list:
all 14 console generator tools, 13 default Trino tools and the optional row tool.
Exercise each operation variant and optional argument, default versus opted-in
discovery, and console versus embedded-runtime ownership where supported.

Required refusal cases include out-of-root/symlink paths; existing outputs;
input nested under a replacement destination; stale/missing fingerprints in
planning approval and stale/missing receipts in preservation consumers;
unknown/malformed arguments; unsafe SQL and excluded catalog/schema; restricted
DB grants; response/input/depth/work/deadline limits; audit admission failure;
transport cancellation/disconnect; and temporary/publication cleanup failure.
Verify no unintended artifacts, no changed old bundle after rollback, no leaked
source literals/secrets in default responses or errors, and no retained
server/session work after teardown. Direct generation/export has no server
planning-receipt gate; verify its client/operator review policy separately.
Do not mistake column selectors for universal table/column authorization.

Default aggregate-only profiling and generator responses must remain row-free.
The explicit opt-in `run_safe_select` intentionally returns bounded masked rows;
verify its masking, budgets, registration opt-in and isolation from generation
and LLM disclosure, rather than requiring that tool to return no rows.

Use bounded small/medium/near-limit load fixtures and pre-allocation refusal
cases. Record duration and the enforced budgets; cooperative deadlines and
payload estimates do not prove an exact peak-memory or hard OS timing ceiling.

Local transformation, common saved-profile consumers and configured SQL sessions
form a separate fictional campaign. Verify local-terminal receipt requirements,
changed-input invalidation, review/validate/execute, capture-once/no-reconnect,
expiry, admission, close/shutdown and cleanup failure. Agents/MCP cannot issue
preservation approval. No plan item activates a gated extension or permits
source rows to enter synthetic output or default MCP responses.

## Environment and deployment runs

- Python 3.11–3.14, locked dependencies and the declared minimum profiles for
  base, parquet, mcp, trino, postgres, openai and gigachat; use the reviewed
  dependency constraints rather than guessing new version pins.
- Real stdio MCP 1.28.1 and the reviewed supported 2.x profile (currently 2.2.0);
  record exact resolved versions. Required Parquet cases need its extra.
  Missing extras must produce safe diagnostics in deliberately minimal installs;
  they are blocked prerequisites in an all-capabilities acceptance run.
- Installed wheel and sdist smoke outside the checkout; three container targets
  × AMD64/ARM64 under non-root/read-only/capability/network/mount restrictions.
  Run actual CLI generation and MCP requests, not only health checks. Images
  without PyArrow test supported workloads and explicit missing-extra behavior;
  Parquet generation uses a properly provisioned installation.
- Disposable fictional PostgreSQL and Trino: component/JDBC/wildcard/query
  acquisition, strict read-only identities, denied access, aggregates → reviewed
  spec → outputs, teardown. No production endpoints or secrets in evidence.
- Actual assistant-client/version smoke with fictional data and human spec
  review, including connection settings, supported client tool policy and final
  artifact checks. Do not replace this with an automated SDK claim.

## Run entry points and evidence

Start with existing suites rather than writing a replacement runner. Useful
anchors include `test_source_output_matrix.py`, `test_universal_business_rules.py`,
`test_portable_scalar_artifacts.py`, `test_generation_modes_and_folder_overwrite.py`,
`test_mcp_client_workflow.py`, `test_mcp_sdk_roundtrip.py`, both MCP transport
suites, `test_cli*.py`, `test_client_*acceptance.py`, `test_transformation_*` and
the disposable-database integration suites. Add missing installed coverage and
a ledger comparison before calling these anchors the complete campaign.

Run `scripts/check_release.sh`, documentation/contract tests, strict MkDocs and
`openspec validate --all --strict` on the final SHA. Use the existing CI,
Containers, Documentation and Security workflows for their actual supported
profiles. A documentation-only skip or a successful container health check
cannot stand in for the workloads above; explicitly run/dispatch the required
existing jobs and add missing workload acceptance where needed.

The report must include each stable case ID and axes, expected outcome,
passed/failed/blocked/not_applicable status, exact SHA/build hashes, environment,
test/command and run URL, artifact hashes and a value-free failure or N/A reason.
Keep source rows, SQL literals, mappings, credentials and provider text out.
Every required cell must pass; a missing run/dependency/environment is blocked.
Contract-inapplicable cases need a reason and their supported alternative, not
silent exclusion. Preserve actual skipped-test reasons in the report.

After any repair, supersede earlier acceptance and rerun affected cases plus
the full final gate on the new SHA. If a release is subsequently authorized,
follow the existing [Release Process](release.md): independent exact-commit
review, four exact-main gates, Ubuntu no-publish hashes, signed acceptance/tag
and public verification. This campaign does not replace or authorize publication.
