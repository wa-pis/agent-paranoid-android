# Change Proposal: 1-1-0-cli-ux

## Summary

Make the public CLI predictable for first-time users and automation before
stable `1.1.0`. Preserve all current command names and compatibility aliases
while fixing misleading file publication, expected-error tracebacks, optional
dependency guidance, help discoverability, and machine-readable diagnostics.

## Motivation

An installed-wheel review of `1.1.0rc1` confirmed that the deterministic happy
path works, but found concrete CLI defects: a requested format can be written
under a conflicting suffix, cross-run `--overwrite` can leave a stale data file
beside new shared sidecars, malformed YAML and Ctrl+C print tracebacks, and
core commands or `doctor` cannot provide a uniform machine contract.

## Scope

In scope:

- Validate single-file output suffixes against the selected format.
- Bind multi-file single-entity overwrite to the same manifest-owned primary
  data file while retaining one-target replacement compatibility.
- Render malformed input, missing extras, cancellation, I/O, provider, and
  unexpected failures without tracebacks unless debug output is requested.
- Add versioned JSON success/error output to core and doctor workflows without
  changing the existing agent JSON schemas.
- Preserve `0` success, `1` validation failure, and `2` expected invocation or
  input failure; add distinct external-service, internal, I/O, and cancellation
  process codes.
- Make root and command help checkout-free, 80-column readable, explicit about
  significant defaults, and recovery-oriented.
- Expose generated shell completion from parser metadata.
- Synchronize CLI, troubleshooting, configuration, stability, changelog,
  roadmap, release checklist, and installed-wheel smoke coverage.

Out of scope:

- Renaming or regrouping the existing public commands.
- Removing the two existing CSV-folder compatibility aliases.
- Adding providers, database integrations, formats, or interactive prompts.
- A new logging framework, progress bars, or a general configuration file.
- Live PostgreSQL, Trino, OpenAI, or GigaChat calls.

## Safety Impact

The change narrows ambiguous filesystem behavior. Format mismatch and
cross-run sidecar replacement fail before generation or publication. Existing
staging, rollback, source-row, privacy, database, and provider boundaries stay
unchanged. Machine output contains bounded summaries and paths, never source
rows, generated rows, provider responses, credentials, tokens, or raw
unexpected exceptions. Profile generation in JSON mode therefore requires
`--output`.

## Compatibility

- Existing command names, arguments, aliases, defaults, generated row schemas,
  agent JSON schemas, MCP tools, and Python APIs remain available.
- Correctly suffixed outputs and same-primary-file `--overwrite` continue to
  work. Previously accepted mislabeled files and cross-file bundle replacement
  fail with migration guidance; this is an intentional integrity correction.
- Existing human output remains the default. `--json` is additive.
- Existing expected codes `0`, `1`, and `2` retain their documented meanings.
  Newly handled external, internal, I/O, and cancellation failures become
  distinguishable without changing successful scripts.
- Implementation changes runtime behavior and the public CLI, so stable
  `1.1.0` requires a new release candidate after review. Tagging and
  publication remain separately authorized release actions.
