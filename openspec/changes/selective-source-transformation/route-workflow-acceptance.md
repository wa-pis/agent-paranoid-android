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
