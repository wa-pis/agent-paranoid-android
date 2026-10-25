# MCP 2 SDK compatibility

The supported minimum is MCP 1.28.1, with Pydantic 2.11.0 in its Python 3.11
minimum profile. MCP 1.0.0 lacks required server/context APIs and is no longer
advertised as supported. The minimum profile must pass the real stdio test,
not skip it. Existing older MCP installations must upgrade the optional extra.

Support the optional MCP SDK 2.2.0 alongside 1.x, without changing tool schemas
or making MCP a base dependency. A dependency range bump alone is insufficient:
the SDK replaces FastMCP, request models, context propagation and error handling.

Keep compatibility adaptations in the shared transport. Preserve bounded stdio
parsing, per-invocation budgets and serialized response limits. SDK 2 unexpected
tool failures must become fixed public errors before the SDK can log their cause.
Intentional safe ToolError messages remain available. No new tools or data access
are introduced. Treat this security-sensitive adapter migration as release-candidate
work and require the supported-Python, minimum-dependency and release gates.
