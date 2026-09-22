# MCP 2 SDK compatibility

Support the optional MCP SDK 2.2.0 alongside 1.x, without changing tool schemas
or making MCP a base dependency. A dependency range bump alone is insufficient:
the SDK replaces FastMCP, request models, context propagation and error handling.

Keep compatibility adaptations in the shared transport. Preserve bounded stdio
parsing, per-invocation budgets and serialized response limits. SDK 2 unexpected
tool failures must become fixed public errors before the SDK can log their cause.
Intentional safe ToolError messages remain available. No new tools or data access
are introduced. Treat this security-sensitive adapter migration as release-candidate
work and require the supported-Python, minimum-dependency and release gates.
