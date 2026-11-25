# Design: Local MCP Client Workflow

## Existing Architecture

Keep the generator workspace boundary separate from Trino credentials and
allowlists. MCP transports register audited application services; safety and
workflow state continue to live in the existing deterministic services.

## Happy Path

1. Install the MCP extra and configure the absolute generator executable and
   `TEST_DATA_AGENT_WORKSPACE_ROOT`. Verify tool discovery via the real client.
2. Place a fictional CSV or safe profile inside that workspace.
3. Call `plan_dataset` with a new or empty agent workspace, explicit count,
   seed, and format. Check that generation has not started.
4. Present metadata and the spec artifact for human review. Inspection returns
   `review.current_spec_sha256`; inspection itself does not approve the plan.
5. After explicit human review, call `approve_dataset_plan` with that exact
   fingerprint. Changed specifications require renewed review.
6. Inspect completion and report counts, validation, provenance, and artifact
   paths. Do not inline datasets into the conversation.

Trino is an optional parallel entry: obtain `profile_table_safe` through the
separate Trino server and pass bounded metadata to `plan_trino_dataset`.
The local onboarding example requires neither database nor provider access.

## Failure And Recovery

On a lost response or interrupted approval, inspect the existing workspace first.
Follow its existing `phase` and `next_action` contract; recover only when the
state permits recovery and use the reviewed fingerprint. Do not unconditionally
repeat approval, create replacement output, or regenerate completed artifacts.
A changed fingerprint requires renewed review. Path and capacity failures must
lead to bounded corrective guidance rather than weakening configured limits.

## Verification

Use the installed MCP SDK client against a subprocess running the real generator
entry point. Bound client waits and always close the session and subprocess.
Use synthetic fixtures, isolated temporary workspaces, and no network services.
Cover tool discovery, plan, inspect, stale-fingerprint rejection, approval,
completion inspection, and recovery after an injected local interruption.
Verify artifact invariants independently of MCP summaries: manifest provenance,
row counts, successful validation, seeded replay, and no source-row reuse.
Check source-cell sentinels are absent from responses and captured logs.

Existing direct-service and bounded-transport tests remain required. Add focused
coverage for meaningful gaps rather than duplicating the entire suite. Document
at least one manual assistant-client acceptance run against the exact candidate
with reviewed metadata; automated stdio coverage does not establish UI usability.
