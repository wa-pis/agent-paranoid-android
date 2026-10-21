# Saved profiles and configured SQL sessions

Discover `transform-batch` subcommand help or the installed common-profile MCP
tools before choosing a route. For SQL, verify `transform-batch query-execute`
or MCP `configured_query_session` exists. Registration does not certify the
separate transformation/session acceptance campaign or authorize a dataset.

Use only administrator-configured, allowlisted read-only sources and bounded
workspace query references. Never supply new endpoints, credentials, arbitrary
SQL or driver code, and never infer database authority from a transformation
request. Keep query text, literals, endpoints and secrets out of model context,
logs, summaries and MCP responses.

Capture once into owned snapshots. In the configured CLI route, the invocation
captures/reviews/approves locally when required and publishes once. With MCP,
open one session and keep its handle, exact digest and narrow approval descriptor.
The local operator uses that descriptor through the existing controlling-TTY
approval CLI; the agent and MCP cannot approve. Review, validation and execution
must reuse the frozen snapshot without reconnecting.

Keep the owned root, fixed receipt name and digest handoff exactly as returned;
do not invent a receipt path or substitute a new snapshot. Private captures are
not permission to export rows in chat. Bound input changes require fresh review
and local approval when preserving. Expired handles require an explicit new
capture and fresh review, never an automatic retry. Report admission refusals
and cleanup failures; do not raise limits, restart the server or remove arbitrary
paths to bypass them. Return bounded value-free metadata only.
