# Private saved-policy route acceptance — 2026-10-01

The installed development candidate completes all twelve combinations of CSV,
Parquet, PostgreSQL captured result and Trino captured result inputs with CSV,
Parquet and PostgreSQL SQL-file outputs. Each uses the same two-row fictional
string/integer replacement fixture, saved YAML, public CLI review, private
command execution, artifact readback, provenance checks and temporary cleanup.
SQL files are checked as text and never executed. Captures use a trusted local
Arrow stream through real query authorization, with no DB/API or monkeypatch.

Command: `PYTHONPATH=<installed-target> python scripts/accept_transformation_routes.py`.
Wheel version1.5.0 is a development artifact, not a released RC.
Wheel SHA256:90b094d4c3066bdfddcd1cf1c84eb37b2871fc0bffa93993038d40575dd1ab93.
Harness SHA256:a9f842ae1baa9f47d4cf8a787704afdb334b0db93a6a280cc5d36d80bfa7d1bc.
Base99cc4d0; Python3.11.2/Darwin arm64. Installed target:
/private/tmp/apa-routes-wheel.n4kBWV/installed.

Result: all12 passed. CLI review digest equals the deterministic request;
review output excludes source and replacement literals. Private file-command
execution reopens fixed snapshots and validates the expected digest. Separate
artifact readback checks every output row/cell, native integer fidelity in
Parquet, exact SQL inserts,100% replacement provenance and unchanged source/
policy bytes; fixture and publication directories are removed.

This basic matrix does not certify all null/decimal/temporal semantics, source
preservation, live query capture, public execution/MCP parity, scale per route
or RC readiness. Prior CSV and PostgreSQL scale evidence was not repeated.
Next: connect common execution/publication contracts to CLI/Python/MCP under
the existing safety amendments and independent activation review.
# MCP service parity follow-up — 2026-10-01

All 12 fictional small route combinations passed with installed CLI and MCP
application-service review parity (same review metadata and snapshot SHA-256),
followed by the existing private executor, full artifact readback, provenance,
unchanged inputs and temporary cleanup. No database access or public execution.
This does not claim new-tool SDK/wire acceptance, preservation approval, full
type coverage or additional scaling acceptance.

- Wheel: `/private/tmp/apa-mcp-review-wheel.L0CxKQ/agent_paranoid_android-1.5.0-py3-none-any.whl`
- Wheel SHA-256: `398914f145cbe95113b7767949db5cd0c7dc1280b83cd737d2af4f23f67dff5c`
- Harness SHA-256: `6c9bb0783050ea20e59bcfe51ece3e903780e4808abcbc9394b58244c918be6d`
- Installed target: `/private/tmp/apa-mcp-review-wheel.L0CxKQ/installed`
- Development version 1.5.0; not a published release candidate.

Additional candidate-source SDK stdio check: the actually registered tool
returns the same shared review; outside-workspace requests fail without the
fictional path marker in wire response or stderr. Source/policy bytes remain
unchanged. `tests/test_transformation_mcp_review.py`: 3 passed. This transport
test is separate from the installed wheel service acceptance above.
