# Design: 1-1-0-cli-ux

## Approach

Keep the current argparse composition and command handlers. Add validation at
the shared single-entity publication boundary, presentation at the existing
CLI presenter boundary, and only the small amount of command-result metadata
needed for a common JSON envelope.

```text
argparse command
    -> existing application handler
    -> deterministic workflow / optional adapter
    -> typed CLI result or typed CLI error
    -> human stderr summary OR one JSON stdout document
```

Do not introduce a command framework or logging dependency. Completion is
derived from the existing argparse parser so it cannot drift into a separately
maintained command inventory.

## Data And Contracts

Add a versioned `CliSuccessResponse` with:

- `schema_version: "1.0"`
- `ok: true`
- `command`
- `exit_code` and `status`
- `artifacts`, containing published local paths only
- an optional bounded command-specific `result`

Retain the existing `CliErrorResponse` shape and extend its enum with
dependency, configuration, I/O, external-service, internal, and cancellation
categories. Existing four enum values remain valid.

`doctor --json` reports each check as one typed status: `available`,
`not_installed`, `not_configured`, `configured_not_tested`, `available`,
`reachable`, `failed`, or `skipped`. Human text states that installed optional
capabilities and local smoke results are not network-reachability checks.

Single-entity generation validates `.csv`, `.json`, `.sql`, or `.parquet`
before work. A lone existing primary target remains replaceable for
compatibility. Once siblings exist, replacement is accepted only when the
manifest identifies the same primary output path and hashes the current
complete bundle.

## Failure Modes

- Mismatched suffix: code `2`, no output or sidecars.
- Existing unrelated bundle or different primary output: code `2`, unchanged
  destination, exact recommendation to use a new directory.
- YAML/JSON parsing or model validation: bounded code `2` error with input
  context, no traceback.
- Missing extra/configuration: bounded typed error and copy-ready install or
  configuration guidance.
- I/O failure: code `74`; existing staged cleanup and rollback run first.
- External provider failure: code `69`; no provider body or exception text.
- Unexpected internal exception: code `70`; fixed message unless `--debug`.
- Ctrl+C: code `130`; no traceback and no final success metadata.

## Alternatives

- Replacing argparse with Typer/Click was rejected: it adds a dependency and
  migration risk without fixing the confirmed defects.
- Moving every command into a new hierarchy was rejected: existing flat names
  are discoverable enough once root help leads with core workflows.
- Keeping a warning window for suffix/overwrite defects was rejected because a
  successful mislabeled or mixed bundle is already an integrity failure in the
  unreleased `1.1.0` line.
- Maintaining checked-in completion scripts was rejected because parser-driven
  generation prevents drift with less code.
