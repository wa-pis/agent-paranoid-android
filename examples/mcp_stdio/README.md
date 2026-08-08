# Runnable MCP Stdio Example

This example uses the installed MCP client library and both installed server
entrypoints over stdio:

```bash
python examples/mcp_stdio/run.py /tmp/agent-paranoid-mcp-example
```

Install the `mcp` and `trino` extras first. The Trino server is configured with
narrow local allowlists and receives a deliberately disallowed catalog request;
the request is rejected before any network connection. The generator server
then plans from the checked-in fictional Trino profile, exposes the spec for
review, binds approval to its SHA-256 digest, and generates eight synthetic JSON
rows.

The automated script stands in for a human only because the profile is a
checked-in synthetic fixture. With a new domain, stop after planning and review
`dataset_spec.yaml` before approving its exact digest. The default aggregate-only
tools return summaries and artifact paths rather than source rows. The explicit
opt-in row-returning tools are disabled here; `run_safe_select` can return
bounded, masked allowed source values and is outside the source-literal-free
guarantee.
