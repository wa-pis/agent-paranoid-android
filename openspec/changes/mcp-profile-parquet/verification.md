# Local verification

2026-11-14, macOS, Python 3.11.2. Tested a locally built wheel against
`main` at `7ca678a866b56fa17eff9bab531961f734b1fd60`. The wheel's runtime
sources were compared to the working change. This is development evidence,
not release or desktop client acceptance.

- The official Python MCP clients 1.28.1 and 2.2.0 used stdio to launch the
  installed `test-data-agent-mcp-generator`. They discovered `profile_parquet`,
  profiled a fictional 10,001-row file with PyArrow 25.0.0 and passed the JSON
  artifact to `plan_dataset`. Inspection confirmed a pending human review
  fingerprint and no generation. Tests checked exact, lower-bound and unknown
  evidence, no retained cell values or embedded metadata, and redacted errors.
- StdIO refusals covered path escapes, symlinks, special files, wrong suffixes,
  malformed input, sensitive values in schema names, a row limit and existing
  output. Local regression tests covered a competing writer and deadline expiry
  during publication. Both SDK versions also passed without PyArrow: the extra
  hint appeared and `profile_csv` still worked.
- The strict OpenSpec check, discovery fixtures, documentation tests, strict
  MkDocs build, lint, type checking and compilation passed. The focused suites
  passed 229 tests on MCP 1 and 75 on MCP 2; the separate no-PyArrow check passed
  on each. An additional transformation regression reached the console for both
  non-preservation cases; the older preservation variants failed at the
  controlling-terminal step. The same failure was reproduced on unchanged
  `main` before reaching MCP.

Reproduce the client test after installing the candidate wheel with
`[mcp,parquet,dev]` in a test environment:

```bash
python -m pytest -q tests/test_acceptance_mcp_permissions.py::test_generator_stdio_parquet_profile_and_review_first_plan
```

For an environment with `[mcp,dev]` and no PyArrow, use
`test_generator_stdio_without_parquet_extra` in the same module.
